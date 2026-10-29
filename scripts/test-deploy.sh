#!/bin/bash
# 测试部署脚本

set -e

echo "=== 磁力搜索部署测试 ==="

# 测试目录
TEST_DIR="/tmp/magnet-test"
DEPLOY_SCRIPT="/var/minis/workspace/magnet-github/scripts/deploy.sh"

# 清理旧测试目录
if [ -d "$TEST_DIR" ]; then
    rm -rf "$TEST_DIR"
fi

# 创建测试目录
mkdir -p "$TEST_DIR/www/cgi-bin"

echo "1. 测试部署脚本..."
if [ -f "$DEPLOY_SCRIPT" ]; then
    echo "✓ 部署脚本存在"
    chmod +x "$DEPLOY_SCRIPT"
else
    echo "✗ 部署脚本不存在"
    exit 1
fi

# 运行部署
echo "2. 执行部署..."
"$DEPLOY_SCRIPT" "$TEST_DIR"

# 检查文件是否存在
echo "3. 检查部署结果..."
if [ -f "$TEST_DIR/www/index.html" ]; then
    echo "✓ index.html 已部署"
else
    echo "✗ index.html 未找到"
fi

for script in search.cgi btsow.cgi add.cgi status.cgi; do
    if [ -f "$TEST_DIR/www/cgi-bin/$script" ]; then
        echo "✓ $script 已部署"
        chmod +x "$TEST_DIR/www/cgi-bin/$script"
    else
        echo "✗ $script 未找到"
    fi
done

# 测试 CGI 脚本语法
echo "4. 测试 CGI 脚本语法..."
for script in "$TEST_DIR/www/cgi-bin/"*.cgi; do
    if [ -x "$script" ]; then
        echo "✓ $script 可执行"
    else
        echo "✗ $script 不可执行"
    fi
done

# 测试页面内容
echo "5. 测试页面内容..."
if [ -f "$TEST_DIR/www/index.html" ]; then
    if grep -q "磁力搜索" "$TEST_DIR/www/index.html"; then
        echo "✓ 页面内容正确"
    else
        echo "✗ 页面内容不正确"
    fi
fi

echo ""
echo "=== 测试完成 ==="
echo "部署目录: $TEST_DIR"
echo "可以手动测试: cd $TEST_DIR && busybox httpd -p 8880 -h www"
echo "清理测试: rm -rf $TEST_DIR"