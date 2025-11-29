#!/bin/bash

# 设置最大并发数
MAX_JOBS=10

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
          bash "$0" $option
        done
        exit 0
        ;;
esac

# 使用城市名作为默认文件名
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

# 新增IP段扫描函数 - 使用线程池优化
scan_ip_with_threadpool() {
    local ip_file=$1
    local city=$2
    local temp_file=$(mktemp)
    local scanned_file=$(mktemp)
    
    echo "开始对 ${city} 的IP进行多线程扫描..."
    echo "最大并发数: $MAX_JOBS"
    
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
    
    # 函数：测试单个IP的连接
    test_ip_connection() {
        local ip_port=$1
        local ip=$(echo "$ip_port" | cut -d: -f1)
        local port=$(echo "$ip_port" | cut -d: -f2)
        
        if nc -w 2 -v -z $ip $port 2>&1 | grep -q "succeeded"; then
            echo "$ip:$port" >> "$scanned_file"
            echo "  ✓ IP可用: $ip:$port"
            return 0
        else
            echo "  × IP不可用: $ip:$port"
            return 1
        fi
    }
    
    # 使用线程池处理IP测试
    local current_jobs=0
    local processed=0
    
    # 导出函数，以便在子shell中使用
    export -f test_ip_connection
    export scanned_file
    
    # 使用xargs创建线程池
    cat "$temp_file" | xargs -I {} -P $MAX_JOBS bash -c 'test_ip_connection "$@"' _ {}
    
    # 将扫描结果保存到正式文件
    if [ -f "$scanned_file" ] && [ -s "$scanned_file" ]; then
        sort "$scanned_file" | uniq > "${ip_file}.scanned"
        local scanned_count=$(wc -l < "${ip_file}.scanned")
        echo "=== 扫描完成 ==="
        echo "总计发现可用IP: $scanned_count 个"
    else
        echo "警告: 未发现可用IP，使用原始IP文件"
        cp "$temp_file" "${ip_file}.scanned"
    fi
    
    rm -f "$temp_file" "$scanned_file"
}

# 修正速度转换函数
convert_speed_to_kb() {
    local speed_str=$1
    local speed_value
    local speed_unit
    local speed_kb=0
    
    # 提取数值和单位
    if [[ "$speed_str" =~ ([0-9.]+)([kKmMgG])? ]]; then
        speed_value="${BASH_REMATCH[1]}"
        speed_unit="${BASH_REMATCH[2]}"
        
        # 转换为KB/s
        case "${speed_unit^^}" in
            "G")
                speed_kb=$(echo "$speed_value * 1024 * 1024" | bc 2>/dev/null || echo "$speed_value * 1048576" | awk '{print $1 * 1048576}')
                ;;
            "M")
                speed_kb=$(echo "$speed_value * 1024" | bc 2>/dev/null || echo "$speed_value * 1024" | awk '{print $1 * 1024}')
                ;;
            "K"|"")
                speed_kb="$speed_value"
                ;;
        esac
    else
        # 如果没有单位，假设是KB/s
        speed_kb="$speed_str"
    fi
    
    # 确保是数字
    if ! [[ "$speed_kb" =~ ^[0-9.]+$ ]]; then
        speed_kb=0
    fi
    
    echo "$speed_kb"
}

# 使用多线程扫描
scan_ip_with_threadpool "$ipfile" "$city"

# 使用扫描后的IP文件
scanned_ipfile="${ipfile}.scanned"
if [ -f "$scanned_ipfile" ]; then
    cat "$scanned_ipfile" > tmp_ipfile
else
    cat "$ipfile" > tmp_ipfile
fi

sort tmp_ipfile | uniq | sed '/^\s*$/d' > py/安徽组播/ip/${city}_config.txt
rm -f tmp_ipfile

# 创建good_ip文件路径
good_ip="py/安徽组播/ip/good_ip.txt"
> "$good_ip"

echo "开始最终连接测试..."
while IFS= read -r ip; do
    tmp_ip=$(echo -n "$ip" | sed 's/:/ /')
    output=$(nc -w 2 -v -z $tmp_ip 2>&1)
    if [[ $output == *"succeeded"* ]]; then
        echo "$ip" >> $good_ip
        echo "  ✓ 连接测试通过: $ip"
    else
        echo "  × 连接测试失败: $ip"
    fi
done < "$scanned_ipfile"

# 清理扫描临时文件
rm -f "$scanned_ipfile"

lines=$(wc -l < $good_ip 2>/dev/null || echo 0)
if [ "$lines" -eq 0 ]; then
    echo "没有可用的IP，退出测试"
    exit 1
fi

echo "最终连接成功 $lines 个IP,开始测速······"

# 测速函数 - 使用多线程
speed_test_with_threadpool() {
    local good_ip_file=$1
    local city=$2
    local time=$3
    local speed_log="speedtest_${city}_${time}.log"
    local temp_dir=$(mktemp -d)
    
    > "$speed_log"
    
    echo "开始多线程测速，最大并发数: $((MAX_JOBS/2))"
    
    # 测速函数
    test_speed() {
        local ip_port=$1
        local city=$2
        local time=$3
        local temp_dir=$4
        local temp_file="${temp_dir}/speed_$$"
        
        local ip=$(echo "$ip_port" | cut -d: -f1)
        local port=$(echo "$ip_port" | cut -d: -f2)
        local url="http://$ip:$port/$stream"
        
        # 使用timeout防止curl卡住
        timeout 30 curl -s "$url" --connect-timeout 5 --max-time 20 -o /dev/null -w "%{speed_download}" > "${temp_file}_speed" 2>&1
        
        local speed=$(cat "${temp_file}_speed" 2>/dev/null)
        local speed_kb=0
        
        if [[ "$speed" =~ ^[0-9.]+$ ]]; then
            # curl返回的是字节/秒，转换为KB/秒
            speed_kb=$(echo "scale=2; $speed / 1024" | bc 2>/dev/null || echo "$speed 1024" | awk '{printf "%.2f", $1 / $2}')
        fi
        
        echo "$ip_port $speed_kb" >> "${temp_file}_result"
        echo "  IP: $ip_port 速度: ${speed_kb}KB/s"
        
        rm -f "${temp_file}_speed"
    }
    
    export -f test_speed
    export stream
    export temp_dir
    
    # 使用xargs进行多线程测速
    cat "$good_ip_file" | xargs -I {} -P $((MAX_JOBS/2)) bash -c 'test_speed "$@"' _ {} "$city" "$time" "$temp_dir"
    
    # 合并结果
    cat "${temp_dir}"/*_result 2>/dev/null | sort -k2 -nr > "$speed_log" 2>/dev/null
    
    # 清理临时文件
    rm -rf "$temp_dir"
    
    echo "$speed_log"
}

# 执行测速
speed_log=$(speed_test_with_threadpool "$good_ip" "$city" "$time")

# 读取测速结果并显示
if [ -f "$speed_log" ]; then
    echo "测速结果:"
    cat "$speed_log" | while read line; do
        ip=$(echo "$line" | awk '{print $1}')
        speed=$(echo "$line" | awk '{print $2}')
        echo "  $ip - ${speed}KB/s"
    done
else
    echo "错误: 测速文件未生成"
    exit 1
fi

# 筛选速度大于100KB/s的IP并保存到结果文件
echo "筛选速度大于100KB/s的IP..."
> "$result_file"
fast_ip_count=0

while IFS= read -r line; do
    ip=$(echo "$line" | awk '{print $1}')
    speed_kb=$(echo "$line" | awk '{print $2}')
    
    # 检查速度是否大于100KB/s
    if (( $(echo "$speed_kb > 100" | bc -l 2>/dev/null || echo "$speed_kb 100" | awk '{if ($1 > $2) print 1; else print 0}') )); then
        echo "$ip" >> "$result_file"
        fast_ip_count=$((fast_ip_count + 1))
        echo "  ✓ 速度合格: $ip - ${speed_kb}KB/s"
    else
        echo "  × 速度不足: $ip - ${speed_kb}KB/s"
    fi
done < "$speed_log"

echo "速度大于100KB/s的IP有 $fast_ip_count 个，已保存到: $result_file"

# 用最快的3个IP生成对应城市的txt文件
echo "测速结果排序"
result_ip="py/安徽组播/ip/result_ip.txt"
sort -k2 -nr "$speed_log" > "$result_ip"

if [ -s "$result_ip" ]; then
    echo "最快的3个IP:"
    head -3 "$result_ip" | while read line; do
        echo "  $line"
    done
    
    ip1=$(head -1 "$result_ip" | awk '{print $1}')
    ip2=$(head -2 "$result_ip" | tail -1 | awk '{print $1}')
    ip3=$(head -3 "$result_ip" | tail -1 | awk '{print $1}')
    
    # 用最快的3个IP生成对应城市的txt文件
    program="py/安徽组播/template/template_${city}.txt"
    if [ -f "$program" ]; then
        sed "s/ipipip/$ip1/g" "$program" > tmp_1.txt
        sed "s/ipipip/$ip2/g" "$program" > tmp_2.txt
        sed "s/ipipip/$ip3/g" "$program" > tmp_3.txt
        echo "${city}-组播1,#genre#" > tmp_all.txt
        cat tmp_1.txt >> tmp_all.txt
        echo "${city}-组播2,#genre#" >> tmp_all.txt
        cat tmp_3.txt >> tmp_all.txt
        grep -vE '/{3}' tmp_all.txt > "py/安徽组播/txt/${city}.txt"
        echo "${city} 测试完成，生成可用文件：'py/安徽组播/txt/${city}.txt'"
    else
        echo "警告: 模板文件 $program 不存在，跳过生成最终文件"
    fi
else
    echo "错误: 没有可用的测速结果"
fi

# 清理所有测试过程中产生的临时文件
echo "清理临时文件..."
rm -rf $good_ip "$speed_log" "$result_ip" tmp_1.txt tmp_2.txt tmp_3.txt tmp_all.txt 2>/dev/null
rm -f tmp_ipfile py/安徽组播/ip/${city}_config.txt 2>/dev/null

echo "所有测试数据已清理完成"
echo "最终结果已保存到: $result_file"

# 显示最终结果
if [ -s "$result_file" ]; then
    echo "最终可用的IP列表:"
    cat "$result_file" | while read ip; do
        # 从测速结果中获取速度
        speed=$(grep "^$ip " "$speed_log" 2>/dev/null | awk '{print $2}' || echo "未知")
        echo "  $ip - ${speed}KB/s"
    done
else
    echo "警告: 没有找到速度大于100KB/s的IP"
fi
