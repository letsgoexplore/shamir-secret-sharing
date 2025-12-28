#!/bin/bash
# 示例使用脚本 - 演示2-of-3 Shamir's Secret Sharing

set -e

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== 2-of-3 Shamir's Secret Sharing 示例 ==="
echo ""

# 生成一个测试密钥（32字节 = 64 hex字符）
echo "1. 生成测试密钥..."
SECRET="0x$(openssl rand -hex 32)"
echo "原始密钥: $SECRET"
echo ""

# 分割密钥
echo "2. 分割密钥为3个分片..."
python3 src/sss_tool.py split "$SECRET" --output test_shares.txt
echo ""

# 显示分片
echo "3. 生成的分片:"
cat test_shares.txt
echo ""

# 提取分片
SHARE1=$(grep "Share 1" test_shares.txt | awk '{print $3}')
SHARE2=$(grep "Share 2" test_shares.txt | awk '{print $3}')
SHARE3=$(grep "Share 3" test_shares.txt | awk '{print $3}')

echo "4. 使用分片1和分片2恢复密钥..."
RECOVERED=$(python3 src/sss_tool.py combine "$SHARE1" "$SHARE2" | grep -A1 "恢复的秘密" | tail -1)
echo "恢复的密钥: $RECOVERED"
echo ""

# 验证
if [ "$SECRET" = "$RECOVERED" ]; then
    echo "✓ 验证成功：恢复的密钥与原始密钥一致！"
else
    echo "✗ 验证失败：密钥不匹配"
    exit 1
fi

echo ""
echo "5. 测试使用分片1和分片3恢复（验证任意2个分片都可恢复）..."
RECOVERED2=$(python3 src/sss_tool.py combine "$SHARE1" "$SHARE3" | grep -A1 "恢复的秘密" | tail -1)
if [ "$SECRET" = "$RECOVERED2" ]; then
    echo "✓ 验证成功：使用分片1+分片3也能正确恢复！"
else
    echo "✗ 验证失败"
    exit 1
fi

echo ""
echo "6. 清理测试文件..."
rm -f test_shares.txt
echo "✓ 测试完成！"

echo ""
echo "=== 重要提示 ==="
echo "- 在实际使用中，请将3个分片安全存储在不同物理位置"
echo "- 任意2个分片即可恢复密钥，但单个分片不泄露任何信息"
echo "- 详细安全建议请参阅 ../docs/SECURITY.md"

