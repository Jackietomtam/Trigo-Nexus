#!/bin/bash

echo "=================================================="
echo "🧪 测试 Edition2 和 Models 页面功能"
echo "=================================================="
echo ""

BASE_URL="http://localhost:5001"

# 颜色代码
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 测试函数
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$response" -eq "$expected_code" ]; then
        echo -e "${GREEN}✓${NC} $name: HTTP $response"
        return 0
    else
        echo -e "${RED}✗${NC} $name: HTTP $response (expected $expected_code)"
        return 1
    fi
}

test_json_data() {
    local name=$1
    local url=$2
    
    data=$(curl -s "$url")
    
    if echo "$data" | python3 -m json.tool > /dev/null 2>&1; then
        count=$(echo "$data" | python3 -c "import sys, json; d = json.load(sys.stdin); print(len(d) if isinstance(d, (list, dict)) else 'N/A')")
        echo -e "${GREEN}✓${NC} $name: Valid JSON (items: $count)"
        return 0
    else
        echo -e "${RED}✗${NC} $name: Invalid JSON"
        return 1
    fi
}

echo "📄 测试页面加载..."
test_endpoint "Edition2 页面" "$BASE_URL/edition2"
test_endpoint "Models 页面" "$BASE_URL/models"
echo ""

echo "🔌 测试 Edition2 API端点..."
test_json_data "Edition2 Prices" "$BASE_URL/api/edition2/prices"
test_json_data "Edition2 Leaderboard" "$BASE_URL/api/edition2/leaderboard"
test_json_data "Edition2 Trades" "$BASE_URL/api/edition2/trades"
test_json_data "Edition2 Chat" "$BASE_URL/api/edition2/chat"
test_json_data "Edition2 History" "$BASE_URL/api/edition2/history"
echo ""

echo "🔌 测试 Models API端点..."
test_json_data "Models API" "$BASE_URL/api/models"
echo ""

echo "🧠 检查 Edition2 AI功能..."
chat_data=$(curl -s "$BASE_URL/api/edition2/chat")
if echo "$chat_data" | grep -q "analysis"; then
    echo -e "${GREEN}✓${NC} AI决策系统正常 (包含分析数据)"
else
    echo -e "${RED}✗${NC} AI决策系统未运行"
fi

if echo "$chat_data" | grep -q "新闻\|情绪"; then
    echo -e "${GREEN}✓${NC} 新闻和情绪分析功能正常"
else
    echo -e "${RED}✗${NC} 新闻和情绪分析未启用"
fi
echo ""

echo "=================================================="
echo "✅ 测试完成！"
echo "=================================================="



