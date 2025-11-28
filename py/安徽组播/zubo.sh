#pwd
if [ $# -eq 0 ]; then
  echo "开始测试······"
  echo "在5秒内输入1~4可选择城市"
  echo "1.安徽电信"
  echo "2.江苏电信"
  echo "3.四川电信"
  read -t 5 -p "超时未输入,将按默认设置测试" city_choice

  if [ -z "$city_choice" ]; then
      echo "未检测到输入,默认测试全部"
      city_choice=0
  fi

else
  city_choice=$1
fi
# 设置城市和相应的stream
case $city_choice in
    1)
        city="安徽电信"
        stream="rtp/238.1.79.27:4328"
        ;;
    2)
        city="江苏电信"
        stream="udp/239.49.8.19:9614"
        ;;
    3)
        city="四川电信"
        stream="udp/239.93.0.169:5140"
        ;;

    0)
        # 逐个处理{ }内每个选项
        for option in {1..3}; do
          bash "$0" $option  # 假定fofa.sh是当前脚本的文件名，$option将递归调用
        done
        exit 0
        ;;
esac

# 新增IP段扫描函数
scan_ip_segments() {
    local ip_file=$1
    local city=$2
    local temp_file=$(mktemp)
    
    echo "开始对 ${city} 的IP进行分段扫描..."
    
    if [ ! -f "$ip_file" ]; then
        echo "错误: IP文件 $ip_file 不存在"
        return 1
    fi
    
    # 读取原始IP并去重
    grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$' "$ip_file" | sort -u > "$temp_file"
    
    declare -A c_segments
    declare -A scanned_c_segments
    
    # 分析C段
    while IFS= read -r line; do
        ip=$(echo "$line" | cut -d: -f1)
        IFS='.' read -r a b c d <<< "$ip"
        c_key="$a.$b.$c"
        c_segments["$c_key"]=1
    done < "$temp_file"
    
    echo "发现 ${#c_segments[@]} 个C段网络"
    
    # 对每个C段进行扫描
    for c_segment in "${!c_segments[@]}"; do
        echo "扫描C段: $c_segment.0/24"
        local segment_found=0
        
        # 首先扫描D段
        for d in $(seq 1 254); do
            test_ip="$c_segment.$d"
            
            # 检查这个IP是否在原始列表中
            if grep -q "^$test_ip:" "$temp_file"; then
                port=$(grep "^$test_ip:" "$temp_file" | head -1 | cut -d: -f2)
                
                # 测试连接
                if timeout 1 bash -c "echo >/dev/tcp/$test_ip/$port" 2>/dev/null; then
                    echo "$test_ip:$port" >> "${ip_file}.scanned"
                    echo "  ✓ D段IP可用: $test_ip:$port"
                    segment_found=1
                fi
            fi
        done
        
        # 如果D段没有找到可用IP，扫描C段的其他IP
        if [ "$segment_found" -eq 0 ]; then
            echo "D段无可用IP，扫描C段其他IP: $c_segment.0/24"
            
            # 扫描该C段中所有在原始列表中的IP
            grep "^$c_segment\." "$temp_file" | while read -r ip_port; do
                test_ip=$(echo "$ip_port" | cut -d: -f1)
                port=$(echo "$ip_port" | cut -d: -f2)
                
                if timeout 1 bash -c "echo >/dev/tcp/$test_ip/$port" 2>/dev/null; then
                    echo "$test_ip:$port" >> "${ip_file}.scanned"
                    echo "  ✓ C段IP可用: $test_ip:$port"
                    segment_found=1
                fi
            done
        fi
        
        scanned_c_segments["$c_segment"]=1
    done
    
    # 如果扫描文件存在且有内容，则使用扫描结果
    if [ -f "${ip_file}.scanned" ] && [ -s "${ip_file}.scanned" ]; then
        local scanned_count=$(wc -l < "${ip_file}.scanned")
        echo "分段扫描完成，发现 $scanned_count 个可用IP"
        # 扫描结果保存在 ${ip_file}.scanned 中，后续代码会使用
    else
        echo "警告: 未发现可用IP，使用原始IP文件"
        cp "$temp_file" "${ip_file}.scanned"
    fi
    
    rm -f "$temp_file"
}

# 使用城市名作为默认文件名，格式为 CityName.ip
time=$(date +%m%d%H%M)
ipfile=py/fofa/ip/${city}.txt
echo "======== 开始检索 ${city} ========"
echo "从 fofa 获取ip+端口"
echo "从 '${ipfile}' 读取ip并添加到检测列表"

# 新增：在读取IP文件后立即进行分段扫描
scan_ip_segments "$ipfile" "$city"

# 修改：使用扫描后的IP文件
scanned_ipfile="${ipfile}.scanned"
if [ -f "$scanned_ipfile" ]; then
    cat "$scanned_ipfile" >> tmp_ipfile
else
    cat "$ipfile" >> tmp_ipfile
fi

sort tmp_ipfile | uniq | sed '/^\s*$/d' > py/安徽组播/ip/${city}_config.txt
rm -f tmp_ipfile

# 创建good_ip文件路径（根据原脚本逻辑推断）
good_ip="py/安徽组播/ip/good_ip.txt"
> "$good_ip"  # 清空文件

while IFS= read -r ip; do
    # 尝试连接 IP 地址和端口号，并将输出保存到变量中
    tmp_ip=$(echo -n "$ip" | sed 's/:/ /')
    output=$(nc -w 1 -v -z $tmp_ip 2>&1)
    # 如果连接成功，且输出包含 "succeeded"，则将结果保存到输出文件中
    if [[ $output == *"succeeded"* ]]; then
        # 使用 awk 提取 IP 地址和端口号对应的字符串，并保存到输出文件中
        echo "$output" | grep "succeeded" | awk -v ip="$ip" '{print ip}' >> $good_ip
    fi
done < "$scanned_ipfile"

# 清理扫描临时文件
rm -f "$scanned_ipfile"

lines=$(wc -l < $good_ip)
echo "连接成功 $lines 个,开始测速······"
i=0
while read line; do
    i=$((i + 1))
    ip=$line
    url="http://$ip/$stream"
    #echo $url
    curl $url --connect-timeout 5 --max-time 40 -o /dev/null >zubo.tmp 2>&1
    a=$(head -n 3 zubo.tmp | awk '{print $NF}' | tail -n 1)  
    echo "第$i/$lines个：$ip    $a"
    echo "$ip    $a" >> speedtest_${city}_$time.log
done < $good_ip

# 推断原脚本中的变量
result_ip="py/安徽组播/ip/result_ip.txt"
py="py"

#cat $good_ip > $ipfile
rm -rf zubo.tmp $good_ip

echo "测速结果排序"
awk '/M|k/{print $2"  "$1}' speedtest_${city}_$time.log | sort -n -r > $result_ip
cat $result_ip
ip1=$(awk 'NR==1{print $2}' $result_ip)
ip2=$(awk 'NR==2{print $2}' $result_ip)
ip3=$(awk 'NR==3{print $2}' $result_ip)
rm -f speedtest_${city}_$time.log $result_ip    

# 用 3 个最快 ip 生成对应城市的 txt 文件
program=py/安徽组播/template/template_${city}.txt
sed "s/ipipip/$ip1/g" $program > tmp_1.txt
sed "s/ipipip/$ip2/g" $program > tmp_2.txt
sed "s/ipipip/$ip3/g" $program > tmp_3.txt
echo "${city}-组播1,#genre#" > tmp_all.txt
cat tmp_1.txt >> tmp_all.txt
echo "${city}-组播2,#genre#" >> tmp_all.txt
cat tmp_3.txt >> tmp_all.txt
grep -vE '/{3}' tmp_all.txt > "py/安徽组播/txt/${city}.txt"
rm -f tmp_1.txt tmp_2.txt tmp_3.txt tmp_all.txt
echo "${city} 测试完成，生成可用文件：'py/安徽组播/txt/${city}.txt'"
