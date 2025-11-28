#!/bin/bash

# 添加IP段扫描函数
scan_ip_segments() {
    local ip_file=$1
    local city=$2
    local good_ip_file=$(mktemp)
    local all_ips_file=$(mktemp)
    
    echo "开始对 ${city} 的IP进行分段扫描..."
    
    # 读取原始IP文件
    if [ ! -f "$ip_file" ]; then
        echo "错误: IP文件 $ip_file 不存在"
        return 1
    fi
    
    # 处理IP文件，提取IP和端口
    while IFS= read -r line; do
        if [[ "$line" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$ ]]; then
            echo "$line" >> "$all_ips_file"
        fi
    done < "$ip_file"
    
    # 按IP地址排序
    sort -t . -k 1,1n -k 2,2n -k 3,3n -k 4,4n "$all_ips_file" > "${all_ips_file}.sorted"
    mv "${all_ips_file}.sorted" "$all_ips_file"
    
    # 分析IP段
    declare -A c_segments  # C段统计
    declare -A d_segments  # D段统计
    
    # 统计C段和D段
    while IFS= read -r ip_port; do
        ip=$(echo "$ip_port" | cut -d: -f1)
        IFS='.' read -r a b c d <<< "$ip"
        c_key="$a.$b.$c"
        d_key="$a.$b.$c.$d"
        
        ((c_segments["$c_key"]++))
        ((d_segments["$d_key"]++))
    done < "$all_ips_file"
    
    echo "发现 ${#c_segments[@]} 个C段网络"
    
    # 对每个C段进行扫描
    for c_segment in "${!c_segments[@]}"; do
        echo "扫描C段: $c_segment.0/24"
        local c_segment_found=0
        
        # 首先扫描D段（1-254）
        for d in $(seq 1 254); do
            test_ip="$c_segment.$d"
            
            # 检查这个IP是否在原始列表中
            if grep -q "^$test_ip:" "$all_ips_file"; then
                port=$(grep "^$test_ip:" "$all_ips_file" | head -1 | cut -d: -f2)
                
                # 测试连接
                if nc -w 1 -v -z $test_ip $port 2>&1 | grep -q "succeeded"; then
                    echo "$test_ip:$port" >> "$good_ip_file"
                    echo "  ✓ D段IP可用: $test_ip:$port"
                    c_segment_found=1
                fi
            fi
        done
        
        # 如果D段没有找到可用IP，扫描C段
        if [ "$c_segment_found" -eq 0 ]; then
            echo "D段无可用IP，开始扫描C段: $c_segment.0/16"
            
            # 扫描C段（这里简化处理，只扫描常见的C段范围）
            for c in $(seq 1 254); do
                for d in $(seq 1 254); do
                    test_ip="${c_segment%.*}.$c.$d"
                    
                    # 检查这个IP是否在原始列表中
                    if grep -q "^$test_ip:" "$all_ips_file"; then
                        port=$(grep "^$test_ip:" "$all_ips_file" | head -1 | cut -d: -f2)
                        
                        # 测试连接
                        if nc -w 1 -v -z $test_ip $port 2>&1 | grep -q "succeeded"; then
                            echo "$test_ip:$port" >> "$good_ip_file"
                            echo "  ✓ C段IP可用: $test_ip:$port"
                            c_segment_found=1
                            break 2  # 找到一个就跳出两层循环
                        fi
                    fi
                done
            done
        fi
    done
    
    # 统计结果
    local good_count=$(wc -l < "$good_ip_file" 2>/dev/null || echo 0)
    echo "分段扫描完成，发现 $good_count 个可用IP"
    
    # 如果找到了可用IP，替换原始文件
    if [ "$good_count" -gt 0 ]; then
        cp "$good_ip_file" "$ip_file"
        echo "已更新IP文件: $ip_file"
    else
        echo "警告: 未发现可用IP，保持原文件"
    fi
    
    # 清理临时文件
    rm -f "$good_ip_file" "$all_ips_file"
}

# 修改原脚本，在读取ip文件后添加分段扫描
# 在以下位置添加调用（约第30行左右，在读取ip文件之后）：
# echo "从 '${ipfile}' 读取ip并添加到检测列表"

# 在cat $ipfile >> tmp_ipfile 之前添加：
echo "开始IP分段扫描..."
scan_ip_segments "$ipfile" "$city"

# 然后继续原有逻辑
cat $ipfile >> tmp_ipfile
sort tmp_ipfile | uniq | sed '/^\s*$/d' > py/安徽组播/ip/${city}_config.txt
rm -f tmp_ipfile

# 其余代码保持不变...
