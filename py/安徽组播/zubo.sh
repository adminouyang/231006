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

# 使用城市名作为默认文件名，格式为 CityName.ip
time=$(date +%m%d%H%M)
ipfile=py/fofa/ip/${city}.txt
echo "======== 开始检索 ${city} ========"
echo "从 fofa 获取ip+端口"
echo "从 '${ipfile}' 读取ip并添加到检测列表"

# 创建结果文件路径
result_file="py/安徽组播/ip/${city}result_ip.txt"
# 确保目录存在
mkdir -p "py/安徽组播/ip/"
# 清空结果文件
> "$result_file"

# 新增IP段扫描函数 - 优化版，扫描所有可用IP
scan_all_available_ips() {
    local ip_file=$1
    local city=$2
    local temp_file=$(mktemp)
    
    echo "开始对 ${city} 的IP进行全量扫描..."
    echo "扫描策略: 先快速扫描D段，再全面扫描C段所有IP"
    
    if [ ! -f "$ip_file" ]; then
        echo "错误: IP文件 $ip_file 不存在"
        return 1
    fi
    
    # 读取原始IP并去重
    grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$' "$ip_file" | sort -u > "$temp_file"
    
    # 统计IP总数
    local total_ips=$(wc -l < "$temp_file")
    echo "发现 $total_ips 个待测试IP"
    
    # 清空扫描结果文件
    > "${ip_file}.scanned"
    
    # 按C段分组处理
    declare -A c_segments
    declare -A c_segment_ips
    
    # 按C段分组IP
    while IFS= read -r line; do
        ip=$(echo "$line" | cut -d: -f1)
        IFS='.' read -r a b c d <<< "$ip"
        c_key="$a.$b.$c"
        c_segments["$c_key"]=1
        c_segment_ips["$c_key"]="${c_segment_ips[$c_key]} $line"
    done < "$temp_file"
    
    echo "发现 ${#c_segments[@]} 个C段网络"
    
    # 对每个C段进行扫描
    local processed=0
    for c_segment in "${!c_segments[@]}"; do
        echo "扫描C段: $c_segment.0/24"
        
        # 获取该C段的所有IP
        local segment_ips=(${c_segment_ips["$c_segment"]})
        local segment_count=${#segment_ips[@]}
        local found_in_segment=0
        
        echo "  本C段有 $segment_count 个IP待测试"
        
        # 先扫描D段（1-254）
        for d in $(seq 1 254); do
            test_ip="$c_segment.$d"
            
            # 检查这个IP是否在当前C段的IP列表中
            for ip_port in "${segment_ips[@]}"; do
                if [[ "$ip_port" == "$test_ip:"* ]]; then
                    port=$(echo "$ip_port" | cut -d: -f2)
                    processed=$((processed + 1))
                    
                    # 测试连接，使用更可靠的测试方法
                    if nc -w 1 -v -z $test_ip $port 2>&1 | grep -q "succeeded"; then
                        echo "$test_ip:$port" >> "${ip_file}.scanned"
                        echo "  ✓ [$processed/$total_ips] IP可用: $test_ip:$port"
                        found_in_segment=$((found_in_segment + 1))
                    else
                        echo "  × [$processed/$total_ips] IP不可用: $test_ip:$port"
                    fi
                    break
                fi
            done
        done
        
        # 扫描C段中可能遗漏的其他IP（非标准D段）
        for ip_port in "${segment_ips[@]}"; do
            # 检查是否已经处理过这个IP
            if ! grep -q "^$ip_port$" "${ip_file}.scanned" 2>/dev/null && 
               ! grep -q "^${ip_port%:*}\." "${ip_file}.scanned" 2>/dev/null; then
                test_ip=$(echo "$ip_port" | cut -d: -f1)
                port=$(echo "$ip_port" | cut -d: -f2)
                
                # 检查IP是否属于当前C段
                if [[ "$test_ip" == "$c_segment."* ]]; then
                    processed=$((processed + 1))
                    
                    if nc -w 1 -v -z $test_ip $port 2>&1 | grep -q "succeeded"; then
                        echo "$test_ip:$port" >> "${ip_file}.scanned"
                        echo "  ✓ [$processed/$total_ips] IP可用: $test_ip:$port"
                        found_in_segment=$((found_in_segment + 1))
                    else
                        echo "  × [$processed/$total_ips] IP不可用: $test_ip:$port"
                    fi
                fi
            fi
        done
        
        echo "  C段 $c_segment.0/24 扫描完成，发现 $found_in_segment 个可用IP"
    done
    
    # 最终统计
    local scanned_count=$(wc -l < "${ip_file}.scanned" 2>/dev/null || echo 0)
    echo "=== 扫描完成 ==="
    echo "总计测试: $processed/$total_ips 个IP"
    echo "初步发现可用IP: $scanned_count 个"
    
    # 如果没有找到可用IP，使用原始文件
    if [ "$scanned_count" -eq 0 ]; then
        echo "警告: 未发现可用IP，使用原始IP文件"
        cp "$temp_file" "${ip_file}.scanned"
    fi
    
    rm -f "$temp_file"
}

# 新增：在读取IP文件后立即进行全量扫描
scan_all_available_ips "$ipfile" "$city"

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

echo "开始最终连接测试..."
while IFS= read -r ip; do
    # 尝试连接 IP 地址和端口号，并将输出保存到变量中
    tmp_ip=$(echo -n "$ip" | sed 's/:/ /')
    output=$(nc -w 1 -v -z $tmp_ip 2>&1)
    # 如果连接成功，且输出包含 "succeeded"，则将结果保存到输出文件中
    if [[ $output == *"succeeded"* ]]; then
        # 使用 awk 提取 IP 地址和端口号对应的字符串，并保存到输出文件中
        echo "$output" | grep "succeeded" | awk -v ip="$ip" '{print ip}' >> $good_ip
        echo "  ✓ 连接测试通过: $ip"
    else
        echo "  × 连接测试失败: $ip"
    fi
done < "$scanned_ipfile"

# 清理扫描临时文件
rm -f "$scanned_ipfile"

lines=$(wc -l < $good_ip)
echo "最终连接成功 $lines 个IP,开始测速······"

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

# 新增：筛选速度大于100KB/s的IP并保存到结果文件
echo "筛选速度大于100KB/s的IP..."
> "$result_file"  # 清空结果文件
fast_ip_count=0

# 解析测速结果，筛选速度大于100KB/s的IP
while IFS= read -r line; do
    ip=$(echo "$line" | awk '{print $1}')
    speed_str=$(echo "$line" | awk '{print $2}')
    
    # 提取速度数值和单位
    speed_value=$(echo "$speed_str" | grep -oE '[0-9.]+')
    speed_unit=$(echo "$speed_str" | grep -oE '[KMGT]?B')
    
    # 转换为KB/s
    speed_kb=0
    if [[ "$speed_unit" == *"M"* ]]; then
        # MB/s 转换为 KB/s
        speed_kb=$(echo "$speed_value * 1024" | bc 2>/dev/null || echo "$speed_value * 1024" | awk '{print $1 * 1024}')
    elif [[ "$speed_unit" == *"K"* ]] || [[ "$speed_unit" == *"B"* ]]; then
        # KB/s 或 B/s
        speed_kb=$speed_value
        if [[ "$speed_unit" == *"B"* ]] && [[ "$speed_unit" != *"K"* ]]; then
            # 如果是B/s，转换为KB/s
            speed_kb=$(echo "$speed_value / 1024" | bc 2>/dev/null || echo "$speed_value / 1024" | awk '{print $1 / 1024}')
        fi
    fi
    
    # 检查速度是否大于100KB/s
    if (( $(echo "$speed_kb > 100" | bc -l 2>/dev/null || echo "$speed_kb 100" | awk '{if ($1 > $2) print 1; else print 0}') )); then
        echo "$ip" >> "$result_file"
        fast_ip_count=$((fast_ip_count + 1))
        echo "  ✓ 速度合格: $ip - $speed_str (约 ${speed_kb%.*}KB/s)"
    else
        echo "  × 速度不足: $ip - $speed_str (约 ${speed_kb%.*}KB/s)"
    fi
done < speedtest_${city}_$time.log

echo "速度大于100KB/s的IP有 $fast_ip_count 个，已保存到: $result_file"

# 用最快的3个IP生成对应城市的txt文件
echo "测速结果排序"
awk '/M|k/{print $2"  "$1}' speedtest_${city}_$time.log | sort -n -r > $result_ip
cat $result_ip
ip1=$(awk 'NR==1{print $2}' $result_ip)
ip2=$(awk 'NR==2{print $2}' $result_ip)
ip3=$(awk 'NR==3{print $2}' $result_ip)

# 用最快的3个IP生成对应城市的txt文件
program=py/安徽组播/template/template_${city}.txt
sed "s/ipipip/$ip1/g" $program > tmp_1.txt
sed "s/ipipip/$ip2/g" $program > tmp_2.txt
sed "s/ipipip/$ip3/g" $program > tmp_3.txt
echo "${city}-组播1,#genre#" > tmp_all.txt
cat tmp_1.txt >> tmp_all.txt
echo "${city}-组播2,#genre#" >> tmp_all.txt
cat tmp_3.txt >> tmp_all.txt
grep -vE '/{3}' tmp_all.txt > "py/安徽组播/txt/${city}.txt"

echo "${city} 测试完成，生成可用文件：'py/安徽组播/txt/${city}.txt'"

# 新增：清理所有测试过程中产生的临时文件
echo "清理临时文件..."
rm -rf zubo.tmp $good_ip speedtest_${city}_$time.log $result_ip tmp_1.txt tmp_2.txt tmp_3.txt tmp_all.txt
# 清理可能存在的其他临时文件
rm -f tmp_ipfile py/安徽组播/ip/${city}_config.txt

echo "所有测试数据已清理完成"
echo "最终结果已保存到: $result_file"
