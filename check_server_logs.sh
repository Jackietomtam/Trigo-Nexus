#!/bin/bash
# 在服务器上执行这些命令来查看修复日志

echo "================================"
echo "📋 查看完整启动日志（最后50行）"
echo "================================"
sudo journalctl -u trigo-nexus -n 50 --no-pager

echo ""
echo "================================"
echo "🔍 查找修复相关日志"
echo "================================"
sudo journalctl -u trigo-nexus -n 100 --no-pager | grep -E "修复|margin_used|fix_margin|Available"

echo ""
echo "================================"
echo "📊 当前服务状态"
echo "================================"
sudo systemctl status trigo-nexus --no-pager

echo ""
echo "================================"
echo "🔍 实时监控（按 Ctrl+C 退出）"
echo "================================"
sudo journalctl -u trigo-nexus -f

