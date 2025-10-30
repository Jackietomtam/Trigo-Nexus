// Alpha Arena 完美复刻

class AlphaArena {
    constructor() {
        this.socket = null;
        this.chart = null;
        this.currentPage = 'live';
        this.currentTimeframe = 'all';
        this.allTrades = [];
        this.allChats = [];  // 保存所有对话数据
        this.expandedChats = new Set();  // 记录已展开的对话
        this.positionsScrollLeft = 0;  // 保存持仓表格滚动位置
        this.positionsScrollMap = {};  // 保存所有AI模型的滚动位置
        // ⚡ 性能优化：节流时间戳
        this.lastChatUpdate = 0;
        this.lastPosUpdate = 0;
        this.init();
    }

    init() {
        this.initSocket();
        this.initChart();
        this.setupEvents();
        this.loadAll();
        
        // 定期更新历史数据（每30秒更新一次图表）
        setInterval(() => {
            this.api('/api/history').then(hist => {
                if (hist) this.updateChart(hist);
            }).catch(e => console.error('更新历史数据失败:', e));
        }, 30000);
    }

    initSocket() {
        this.socket = io();
        this.socket.on('connect', () => console.log('✓ 已连接'));
        
        // 根据当前页面监听对应的事件
        const currentPath = window.location.pathname;
        if (currentPath.includes('/edition1')) {
            this.socket.on('edition1_update', (d) => this.onUpdate(d));
            console.log('监听 edition1_update 事件');
        } else if (currentPath.includes('/edition2')) {
            this.socket.on('edition2_update', (d) => this.onUpdate(d));
            console.log('监听 edition2_update 事件');
        } else {
            // 默认监听两个事件
            this.socket.on('edition1_update', (d) => this.onUpdate(d));
            this.socket.on('edition2_update', (d) => this.onUpdate(d));
        }
        
        // 兼容旧的 market_update 事件
        this.socket.on('market_update', (d) => this.onUpdate(d));
    }

    initChart() {
        const ctx = document.getElementById('mainChart');
        if (!ctx) return;

        this.chart = new Chart(ctx, {
            type: 'line',
            data: { labels: [], datasets: [] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            color: '#999',
                            font: { size: 10, weight: '600' },
                            padding: 12,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.9)',
                        borderColor: '#333',
                        borderWidth: 1,
                        titleColor: '#fff',
                        bodyColor: '#ccc',
                        padding: 10,
                        cornerRadius: 4
                    }
                },
                scales: {
                    x: {
                        grid: { color: '#1a1a1a', drawBorder: false },
                        ticks: { 
                            color: '#666', 
                            font: { size: 9 }, 
                            maxTicksLimit: 12,
                            autoSkip: true,
                            maxRotation: 45,
                            minRotation: 0
                        }
                    },
                    y: {
                        grid: { color: '#1a1a1a', drawBorder: false },
                        ticks: {
                            color: '#666',
                            font: { size: 9 },
                            callback: (v) => '$' + v.toLocaleString()
                        }
                    }
                }
            }
        });
    }

    setupEvents() {
        // 导航 - 阻止默认跳转
        const navLive = document.getElementById('navLive');
        const navMod = document.getElementById('navModels');
        
        if (navLive) {
            navLive.addEventListener('click', (e) => {
                e.preventDefault();
                this.showPage('live');
            });
        }
        
        if (navMod) {
            navMod.addEventListener('click', (e) => {
                e.preventDefault();
                // 直接跳转到独立的 models 页面
                window.location.href = '/models';
            });
        }

        // 控制按钮已移除

        // 详情标签
        document.querySelectorAll('.dtab').forEach(t => {
            t.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Tab clicked:', t.dataset.tab);
                
                document.querySelectorAll('.dtab').forEach(x => x.classList.remove('active'));
                document.querySelectorAll('.detail-pane').forEach(x => x.classList.remove('active'));
                
                t.classList.add('active');
                const tab = t.dataset.tab;
                const paneId = 'pane' + tab.charAt(0).toUpperCase() + tab.slice(1);
                const pane = document.getElementById(paneId);
                
                console.log('Looking for pane:', paneId, 'Found:', !!pane);
                
                if (pane) {
                    pane.classList.add('active');
                    console.log('Activated pane:', paneId);
                    if (tab === 'positions') {
                        // 需求：点击“持仓”直接查看“两位AI”的表现
                        // 清除已选AI，避免单模型覆盖汇总视图
                        this.selectedId = null;
                        this.loadAllPositions();
                        // 平滑滚动到持仓列表区域
                        const list = document.getElementById('positionsList');
                        if (list && list.scrollIntoView) {
                            list.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }
                } else {
                    console.log('找不到面板:', paneId);
                }
            });
        });

        // 图表控制
        document.querySelectorAll('.ctrl-chart[data-time]').forEach(b => {
            b.addEventListener('click', () => this.changeTime(b.dataset.time));
        });

        // 筛选
        document.getElementById('filterModel')?.addEventListener('change', () => this.filterTrades());
        document.getElementById('filterChat')?.addEventListener('change', () => this.filterChats());
    }

    async loadAll() {
        try {
            const [priceData, lb, trades, chats, hist] = await Promise.all([
                this.api('/api/prices'),
                this.api('/api/leaderboard'),
                this.api('/api/trades'),
                this.api('/api/chat'),
                this.api('/api/history')
            ]);

            console.log('加载数据:', {trades: trades?.length, chats: chats?.length});
            
            this.updateTicker(priceData.prices, priceData.changes);
            this.updateCards(lb);
            this.updateChart(hist);
            this.allTrades = trades || [];
            this.allChats = chats || [];
            this.updateTrades(trades || []);
            this.updateChats(chats || []);
            this.updateFilters(lb);
        } catch (e) {
            console.error('加载失败:', e);
        }
    }

    async api(url) {
        // 自动检测当前是Edition1还是Edition2
        const currentPath = window.location.pathname;
        let apiPrefix = '';
        
        if (currentPath.includes('/edition1')) {
            apiPrefix = '/edition1';
        } else if (currentPath.includes('/edition2')) {
            apiPrefix = '/edition2';
        }
        
        // 如果URL以/api/开头，添加edition前缀
        if (url.startsWith('/api/edition1/') || url.startsWith('/api/edition2/')) {
            // 已包含完整前缀，保持不变
        } else if (url.startsWith('/api/')) {
            url = url.replace('/api/', `/api${apiPrefix}/`);
        }
        
        const res = await fetch(url);
        return res.json();
    }

    onUpdate(d) {
        if (d.prices) this.updateTicker(d.prices, d.changes);
        if (d.leaderboard) this.updateCards(d.leaderboard);
        if (d.trades) {
            this.allTrades = d.trades;
            this.filterTrades();  // 应用筛选
        }
        if (d.history) this.updateChart(d.history);
        
        // ⚡ 优化1：节流聊天数据请求（最多5秒刷新一次）
        const now = Date.now();
        if (!this.lastChatUpdate || now - this.lastChatUpdate > 5000) {
            this.lastChatUpdate = now;
            this.api('/api/chat').then(c => {
                this.allChats = c;
                this.filterChats();
            });
        }
        
        // ⚡ 持仓数据实时更新（2秒刷新间隔）
        const posPane = document.getElementById('panePositions');
        const isPosActive = posPane && posPane.classList.contains('active');
        const hasSelectedAI = this.selectedId !== null;
        
        // 如果持仓面板激活 或 选中了某个AI，都要更新
        if (isPosActive || hasSelectedAI) {
            if (!this.lastPosUpdate || now - this.lastPosUpdate > 2000) {
                this.lastPosUpdate = now;
                
                // 更新汇总持仓（如果面板激活）
                if (isPosActive) {
                    this.loadAllPositions();
                }
                
                // 更新单个AI持仓（如果选中了AI）
                if (hasSelectedAI) {
                    this.api(`/api/trader/${this.selectedId}`).then(data => {
                        if (data && data.account) {
                            this.showPositions(data);
                        }
                    });
                }
            }
        }
    }

    updateTicker(prices, changes) {
        const c = document.getElementById('tickerScroll');
        if (!c) return;
        changes = changes || {};
        
        // 保存旧价格用于比较
        if (!this.lastPrices) this.lastPrices = {};
        
        // 使用真实的CoinMarketCap图标
        const icons = { 
            BTC: '<img src="https://s2.coinmarketcap.com/static/img/coins/64x64/1.png" width="24" height="24" style="border-radius:50%">',
            ETH: '<img src="https://s2.coinmarketcap.com/static/img/coins/64x64/1027.png" width="24" height="24" style="border-radius:50%">',
            SOL: '<img src="https://s2.coinmarketcap.com/static/img/coins/64x64/5426.png" width="24" height="24" style="border-radius:50%">',
            BNB: '<img src="https://s2.coinmarketcap.com/static/img/coins/64x64/1839.png" width="24" height="24" style="border-radius:50%">',
            DOGE: '<img src="https://s2.coinmarketcap.com/static/img/coins/64x64/74.png" width="24" height="24" style="border-radius:50%">',
            XRP: '<img src="https://s2.coinmarketcap.com/static/img/coins/64x64/52.png" width="24" height="24" style="border-radius:50%">'
        };
        
        let h = '';
        for (const [sym, price] of Object.entries(prices)) {
            const chg = changes[sym] || 0;
            const cls = chg >= 0 ? 'positive' : 'negative';
            const sign = chg >= 0 ? '+' : '';
            
            // 检测价格变动方向
            const oldPrice = this.lastPrices[sym];
            let animClass = '';
            if (oldPrice !== undefined && oldPrice !== price) {
                if (price > oldPrice) {
                    animClass = 'price-flash-up flip-up';
                } else if (price < oldPrice) {
                    animClass = 'price-flash-down flip-down';
                }
            }
            
            h += `
                <div class="ticker-item">
                    <span class="ticker-icon">${icons[sym] || '⚪'}</span>
                    <div class="ticker-info">
                        <div class="ticker-label">${sym}</div>
                        <div class="ticker-price ${animClass}" data-symbol="${sym}">$${this.fp(price)}</div>
                    </div>
                    <div class="ticker-change ${cls}">${sign}${chg.toFixed(2)}%</div>
                </div>
            `;
            
            // 保存当前价格
            this.lastPrices[sym] = price;
        }
        c.innerHTML = h;
        
        // 清除动画类（动画结束后移除，以便下次可以重新触发）
        setTimeout(() => {
            c.querySelectorAll('.ticker-price').forEach(el => {
                el.classList.remove('flip-up', 'flip-down', 'price-flash-up', 'price-flash-down');
            });
        }, 600);
        // 让整条卡片可点击以展开/收起所有详情
        document.querySelectorAll('#chatList .chat-entry').forEach(card => {
            card.addEventListener('click', (e) => {
                // 如果点击的是summary本身，交给浏览器默认行为即可
                if (e.target && (e.target.tagName === 'SUMMARY' || e.target.closest('summary'))) return;
                const dets = card.querySelectorAll('details');
                const anyOpen = Array.from(dets).some(d => d.open);
                dets.forEach(d => d.open = !anyOpen);
            });
        });
    }

    updateCards(lb) {
        const c = document.getElementById('modelCards');
        if (!c || !lb) return;

        // 过滤掉基准账户，仅展示两位AI
        const aiList = lb.filter(x => x.name !== 'BTC BUY&HOLD');

        // 更新最高/最低（基于两位AI）
        if (aiList.length > 0) {
            const hi = aiList[0];
            const lo = aiList[aiList.length - 1];
            document.getElementById('highestInfo').textContent = 
                `${hi.name} $${this.fn(hi.total_value)} ${hi.profit_loss_percent >= 0 ? '+' : ''}${hi.profit_loss_percent.toFixed(2)}%`;
            document.getElementById('lowestInfo').textContent = 
                `${lo.name} $${this.fn(lo.total_value)} ${lo.profit_loss_percent >= 0 ? '+' : ''}${lo.profit_loss_percent.toFixed(2)}%`;
        }

        // 使用AI模型的真实logo
        const modelIcons = {
            'QWEN3 MAX': '<img src="/static/img/ai/qwen.png?v=2" alt="Qwen" width="32" height="32" style="border-radius:6px;object-fit:contain;">',
            'DEEPSEEK V3.2': '<img src="/static/img/ai/deepseek.jpg" alt="DeepSeek" width="32" height="32" style="border-radius:6px;object-fit:cover;">',
            'BTC BUY&HOLD': '<img src="https://s2.coinmarketcap.com/static/img/coins/64x64/1.png" alt="Bitcoin" width="32" height="32" style="border-radius:50%;">'
        };
        
        let h = '';
        aiList.forEach((t, i) => {
            // ✅ 强制使用后端统一数据，不做任何前端计算
            const pnlAmount = t.total_pnl_amount || 0;
            const cls = pnlAmount >= 0 ? 'positive' : 'negative';
            const sign = pnlAmount >= 0 ? '+' : '-';
            const icon = modelIcons[t.name] || '⚪';
            
            const cardClass = 'model-card';
            const clickHandler = `onclick="app.selectModel(${t.id})"`;
            
            h += `
                <div class="${cardClass}" ${clickHandler}>
                    ${icon}
                    <div class="model-name">${t.name}</div>
                    <div class="model-value">$${this.fn(t.total_value)}</div>
                    <div class="model-change ${cls}">${sign}$${this.fn(Math.abs(pnlAmount))}</div>
                </div>
            `;
        });
        c.innerHTML = h;
    }

    updateChart(hist) {
        if (!this.chart || !hist) return;

        // 模型特定颜色
        const modelColors = {
            'QWEN3 MAX': '#8844ff',      // 紫色
            'DEEPSEEK V3.2': '#0088ff',  // 蓝色
            'BTC BUY&HOLD': '#FFB800'    // 金色
        };
        const defaultColors = ['#ff8844', '#888888', '#ff0088', '#44ffff', '#ffff00'];
        
        const ds = [];
        let labels = [];
        let maxLen = 0;

        Object.keys(hist).forEach((name, idx) => {
            const data = hist[name];
            if (!data || data.length === 0) return;
            if (data.length > maxLen) {
                maxLen = data.length;
                labels = data.map(d => {
                    const dt = new Date(d.timestamp * 1000);
                    const m = dt.getMonth() + 1;
                    const day = dt.getDate();
                    const h = ('0' + dt.getHours()).slice(-2);
                    const min = ('0' + dt.getMinutes()).slice(-2);
                    return `${m}/${day} ${h}:${min}`;
                });
            }
            
            // 确定颜色
            const isBtcBenchmark = name === 'BTC BUY&HOLD';
            const color = modelColors[name] || defaultColors[idx % defaultColors.length];
            
            ds.push({
                label: name,
                data: data.map(d => d.value),
                borderColor: color,
                backgroundColor: 'transparent',
                borderWidth: isBtcBenchmark ? 2 : 2.5,
                borderDash: isBtcBenchmark ? [10, 5] : [], // BTC用虚线
                tension: 0.35,
                pointRadius: 0,
                pointHoverRadius: 4,
                pointHoverBackgroundColor: color
            });
        });

        // 根据数据量动态调整x轴刻度
        const ticksLimit = maxLen > 200 ? 15 : (maxLen > 100 ? 12 : 10);
        this.chart.options.scales.x.ticks.maxTicksLimit = ticksLimit;
        
        this.chart.data.labels = labels;
        this.chart.data.datasets = ds;
        this.chart.update('none');
    }

    updateTrades(trades) {
        const c = document.getElementById('tradeList');
        if (!c) return;
        if (!trades || trades.length === 0) {
            c.innerHTML = '<div class="empty-state">暂无交易记录</div>';
            return;
        }

        let h = '';
        trades.slice(0, 100).forEach(tr => {
            const isOpen = tr.action && (tr.action.includes('open'));
            const isClose = tr.action && (tr.action.includes('close'));
            const sideText = tr.side === 'long' ? 'LONG' : 'SHORT';
            const sideClass = tr.side === 'long' ? 'positive' : 'negative';
            const actionLabel = isOpen ? '开仓' : (isClose ? '平仓' : '交易');
            const pnl = tr.pnl || 0;
            const pnlClass = pnl >= 0 ? 'positive' : 'negative';
            
            h += `
                <div class="trade-entry">
                    <div class="trade-head">
                        <span class="trade-model" style="display:flex;align-items:center;gap:6px;">${this.getAILogoSmall(tr.trader_name)} ${tr.trader_name}</span>
                        <span class="trade-time">${tr.datetime}</span>
                    </div>
                    <div style="font-size:13px;margin-bottom:12px;color:#fff;font-weight:600;">
                        <span class="${sideClass}" style="font-weight:700;">${sideText}</span> ${this.getCoinIcon(tr.symbol)} ${tr.symbol} · ${actionLabel} · ${tr.leverage}X杠杆
                    </div>
                    <div class="trade-grid">
                        ${isOpen ? `
                        <div class="trade-field">
                            <span class="field-label">开仓时间</span>
                            <span class="field-value">${tr.datetime}</span>
                        </div>
                        <div class="trade-field">
                            <span class="field-label">入场价</span>
                            <span class="field-value">$${this.fp(tr.price || tr.entry_price)}</span>
                        </div>
                        <div class="trade-field">
                            <span class="field-label">数量</span>
                            <span class="field-value">${(tr.quantity||0).toFixed(4)}</span>
                        </div>
                        ` : ''}
                        ${isClose ? `
                        <div class="trade-field">
                            <span class="field-label">开仓时间</span>
                            <span class="field-value">${tr.entry_datetime || '—'}</span>
                        </div>
                        <div class="trade-field">
                            <span class="field-label">平仓时间</span>
                            <span class="field-value">${tr.exit_datetime || tr.datetime}</span>
                        </div>
                        <div class="trade-field">
                            <span class="field-label">持仓时长</span>
                            <span class="field-value">${this.formatHoldingTime(tr.holding_seconds||0)}</span>
                        </div>
                        <div class="trade-field">
                            <span class="field-label">入场价</span>
                            <span class="field-value">$${this.fp(tr.entry_price)}</span>
                        </div>
                        <div class="trade-field">
                            <span class="field-label">出场价</span>
                            <span class="field-value">$${this.fp(tr.exit_price)}</span>
                        </div>
                        <div class="trade-field">
                            <span class="field-label">数量</span>
                            <span class="field-value">${(tr.quantity||0).toFixed(4)}</span>
                        </div>
                        <div class="trade-field">
                            <span class="field-label">盈亏</span>
                            <span class="field-value ${pnlClass}" style="font-weight:700;">${pnl>=0?'+':''}$${this.fn(Math.abs(pnl))}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        });
        c.innerHTML = h;
        const countEl = document.getElementById('tradeCount');
        if (countEl) countEl.textContent = `显示最近 ${Math.min(trades.length, 100)} 笔交易`;
    }

    updateChats(chats) {
        const c = document.getElementById('chatList');
        if (!c) return;
        if (!chats || chats.length === 0) {
            c.innerHTML = '<div class="empty-state">AI 正在思考中...</div>';
            return;
        }

        let h = '';
        chats.forEach((ch, idx) => {
            const cls = ch.profit_loss_percent >= 0 ? 'positive' : 'negative';
            const sign = ch.profit_loss_percent >= 0 ? '+' : '';
            const uid = `chat_${ch.timestamp || idx}`;
            const isExpanded = this.expandedChats.has(uid);
            h += `
                <div class="chat-entry" data-uid="${uid}">
                    <div class="chat-header">
                        <span class="chat-model" style="display:flex;align-items:center;gap:6px;">${this.getAILogoSmall(ch.trader)} ${ch.trader}</span>
                        <span class="chat-time">${ch.datetime || new Date(ch.timestamp * 1000).toLocaleString('zh-CN')}</span>
                    </div>
                    <div class="chat-body">${(ch.analysis || '分析中...')}</div>
                    ${ch.total_value ? `
                        <div class="chat-stats">
                            账户: $${this.fn(ch.total_value)} 
                            <span class="${cls}">(${sign}${ch.profit_loss_percent.toFixed(2)}%)</span>
                            ${ch.positions ? ` | 持仓: ${ch.positions}` : ''}
                        </div>
                    ` : ''}
                    ${ch.user_prompt || ch.trading_decision ? `
                    <div class="chat-expand" style="display:${isExpanded ? 'block' : 'none'};margin-top:12px;border-top:1px solid #1a1a1a;padding-top:12px;">
                        ${ch.user_prompt ? `
                        <div style="margin-bottom:12px;">
                            <div style="color:#00ccff;font-weight:700;margin-bottom:6px;">▶ USER_PROMPT</div>
                            <pre style="white-space:pre-wrap;color:#bbb;font-size:11px;line-height:1.6;">${this.escapeHtml(ch.user_prompt)}</pre>
                        </div>
                        ` : ''}
                        ${ch.trading_decision ? `
                        <div>
                            <div style="color:#00ff88;font-weight:700;margin-bottom:6px;">▶ TRADING_DECISIONS</div>
                            ${this.renderTradingDecisions(ch.trading_decision)}
                        </div>
                        ` : ''}
                    </div>
                    ` : ''}
                </div>
            `;
        });
        c.innerHTML = h;
        
        // 渲染后立即恢复所有展开状态（修复自动收回问题）
        setTimeout(() => {
            this.expandedChats.forEach(uid => {
                const card = c.querySelector(`[data-uid="${uid}"]`);
                if (card) {
                    const expand = card.querySelector('.chat-expand');
                    if (expand) {
                        expand.style.display = 'block';
                    }
                }
            });
        }, 0);
        
        // 点击卡片切换展开/收起，并记录状态
        c.querySelectorAll('.chat-entry').forEach((card) => {
            card.style.cursor = 'pointer';
            card.addEventListener('click', (e) => {
                // 避免点击pre时触发
                if (e.target.tagName === 'PRE') return;
                const uid = card.getAttribute('data-uid');
                const expand = card.querySelector('.chat-expand');
                if (expand) {
                    const isVisible = expand.style.display !== 'none';
                    expand.style.display = isVisible ? 'none' : 'block';
                    // 记录状态
                    if (isVisible) {
                        this.expandedChats.delete(uid);
                    } else {
                        this.expandedChats.add(uid);
                    }
                }
            });
        });
    }

    renderTradingDecisions(decision) {
        if (!decision) return '';
        
        // 如果是多币种决策格式，过滤掉没有仓位的HOLD信号
        if (decision.decisions && typeof decision.decisions === 'object') {
            const filtered = {};
            for (const [symbol, trade] of Object.entries(decision.decisions)) {
                const signal = (trade.signal || 'hold').toLowerCase();
                const quantity = trade.quantity || 0;
                
                // 只显示：1. 有仓位的HOLD  2. 任何LONG/SHORT信号
                if (signal === 'hold' && quantity === 0) {
                    continue; // 跳过没有仓位的HOLD
                }
                filtered[symbol] = trade;
            }
            
            // 如果过滤后没有任何决策，显示观望信息
            if (Object.keys(filtered).length === 0) {
                return `<div style="color:#666;font-size:12px;padding:12px;text-align:center;font-style:italic;">观望中，等待交易机会...</div>`;
            }
            
            // 构造过滤后的决策对象
            const filteredDecision = {
                analysis: decision.analysis,
                decisions: filtered
            };
            return `<pre style="white-space:pre-wrap;color:#bbb;font-size:11px;line-height:1.6;">${this.escapeHtml(JSON.stringify(filteredDecision, null, 2))}</pre>`;
        }
        
        // 其他格式直接显示
        return `<pre style="white-space:pre-wrap;color:#bbb;font-size:11px;line-height:1.6;">${this.escapeHtml(JSON.stringify(decision, null, 2))}</pre>`;
    }

    escapeHtml(s) {
        if (!s) return '';
        return s
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    updateFilters(lb) {
        if (!lb) return;
        const mf = document.getElementById('filterModel');
        const cf = document.getElementById('filterChat');
        let opts = '<option value="all">ALL MODELS</option>';
        lb.forEach(t => {
            // 排除 BTC BUY&HOLD（它不是AI模型）
            if (t.name && t.name.includes('BTC BUY&HOLD')) return;
            opts += `<option value="${t.name}">${t.name}</option>`;
        });
        if (mf) mf.innerHTML = opts;
        if (cf) cf.innerHTML = opts;
    }

    filterTrades() {
        const f = document.getElementById('filterModel')?.value;
        if (!f) return;
        let filtered = this.allTrades;
        if (f !== 'all') filtered = this.allTrades.filter(t => t.trader_name === f);
        this.updateTrades(filtered);
    }

    filterChats() {
        const f = document.getElementById('filterChat')?.value;
        if (!f) return;
        let filtered = this.allChats;
        if (f !== 'all') filtered = this.allChats.filter(c => c.trader === f);
        this.updateChats(filtered);
    }

    async changeTime(t) {
        this.currentTimeframe = t;
        document.querySelectorAll('.ctrl-chart[data-time]').forEach(b => {
            b.classList.toggle('active', b.dataset.time === t);
        });
        
        // 重新加载历史数据
        const hist = await this.api(`/api/history?timeframe=${t}`);
        
        // 调试：输出数据量
        console.log(`📊 切换时间范围到 ${t}:`, Object.entries(hist).map(([name, data]) => 
            `${name}: ${data.length}个数据点, 时间范围: ${data[0]?.timestamp ? new Date(data[0].timestamp * 1000).toLocaleString() : 'N/A'} - ${data[data.length-1]?.timestamp ? new Date(data[data.length-1].timestamp * 1000).toLocaleString() : 'N/A'}`
        ));
        
        // 筛选数据
        let filtered = {};
        if (t === '4h') {
            const now = Date.now() / 1000;
            const cutoff = now - (4 * 3600);
            for (const [name, data] of Object.entries(hist)) {
                filtered[name] = data.filter(d => d.timestamp >= cutoff);
            }
            console.log(`📊 4H筛选后:`, Object.entries(filtered).map(([name, data]) => `${name}: ${data.length}个数据点`));
        } else {
            filtered = hist;
        }
        
        this.updateChart(filtered);
    }

    showPage(page) {
        this.currentPage = page;
        document.querySelectorAll('.page-content').forEach(p => p.style.display = 'none');
        const pageEl = document.getElementById('page' + page.charAt(0).toUpperCase() + page.slice(1));
        if (pageEl) {
            pageEl.style.display = 'block';
        } else {
            console.log('找不到页面:', page);
        }
        
        // 更新导航状态
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.getElementById('nav' + page.charAt(0).toUpperCase() + page.slice(1))?.classList.add('active');
    }

    async loadLeaderboard() {
        const data = await this.api('/api/leaderboard_full');
        const tbody = document.getElementById('lbTableBody');
        if (!tbody || !data) return;
        
        let h = '';
        data.forEach(r => {
            const retCls = r.return_percent >= 0 ? 'positive' : 'negative';
            const pnlCls = r.total_pnl >= 0 ? 'positive' : 'negative';
            h += `
                <tr>
                    <td>${r.rank}</td>
                    <td>${r.model}</td>
                    <td>$${this.fn(r.acct_value)}</td>
                    <td class="${retCls}">${r.return_percent >= 0 ? '+' : ''}${r.return_percent.toFixed(2)}%</td>
                    <td class="${pnlCls}">${r.total_pnl >= 0 ? '+' : ''}$${this.fn(Math.abs(r.total_pnl))}</td>
                    <td>$${this.fn(r.fees)}</td>
                    <td>${r.win_rate.toFixed(1)}%</td>
                    <td>$${this.fn(r.biggest_win)}</td>
                    <td class="negative">-$${this.fn(Math.abs(r.biggest_loss))}</td>
                    <td>${r.sharpe.toFixed(3)}</td>
                    <td>${r.trades}</td>
                </tr>
            `;
        });
        tbody.innerHTML = h;
    }

    async loadAllPositions() {
        // 拉取所有AI的持仓并汇总渲染（剔除BTC基准，只展示两位AI）
        const lb = await this.api('/api/leaderboard');
        const c = document.getElementById('positionsList');
        if (!lb || !c) return;
        const aiList = lb.filter(x => x.name !== 'BTC BUY&HOLD');
        const lbMap = Object.fromEntries(aiList.map(x => [String(x.id), x]));
        
        // 保存所有表格的滚动位置
        c.querySelectorAll('.pos-table-wrapper').forEach(wrapper => {
            const modelName = wrapper.getAttribute('data-model');
            if (modelName && wrapper.scrollLeft > 0) {
                this.positionsScrollMap[modelName] = wrapper.scrollLeft;
            }
        });
        
        // ⚡ 性能优化：并行请求所有AI的详情数据
        const detailPromises = aiList.map(m => this.api(`/api/trader/${m.id}`));
        const details = await Promise.all(detailPromises);
        
        let h = '';
        details.forEach((detail, idx) => {
            const m = aiList[idx];
            // 将排行榜的统一口径数值注入，确保与左下角一致
            if (detail && detail.metrics) {
                detail.metrics.total_pnl_amount = m.total_pnl_amount;
                detail.metrics.total_value = m.total_value;
            }
            if (detail && detail.account) {
                detail.account.total_pnl_amount = m.total_pnl_amount;
                detail.account.total_value = m.total_value;
            }
            h += this.renderPositionsBlock(detail);
        });
        c.innerHTML = h || '<div class="empty-state">暂无持仓</div>';
        
        // 恢复所有表格的滚动位置
        setTimeout(() => {
            c.querySelectorAll('.pos-table-wrapper').forEach(wrapper => {
                const modelName = wrapper.getAttribute('data-model');
                if (modelName && this.positionsScrollMap[modelName]) {
                    wrapper.scrollLeft = this.positionsScrollMap[modelName];
                }
                // 添加滚动监听
                wrapper.addEventListener('scroll', () => {
                    this.positionsScrollMap[modelName] = wrapper.scrollLeft;
                });
            });
        }, 0);
    }

    renderPositionsBlock(data) {
        if (!data) return '';
        // 统一数据源：优先使用 account，如果没有则使用 metrics
        const account = data.account || {};
        const metrics = data.metrics || {};
        const displayName = account.name || metrics.trader_name || '';
        // ✅ 强制使用后端统一数据，不做任何前端计算（优先account，其次metrics）
        const unrealizedPnl = account.unrealized_pnl ?? metrics.unrealized_pnl ?? 0;
        const totalPnlAmount = account.total_pnl_amount ?? metrics.total_pnl_amount ?? 0;
        const positions = data.positions || [];
        let h = `
            <div class="pos-card" style="width:100%;box-sizing:border-box;">
                <div class="pos-header" style="margin-bottom:16px;">
                    <div class="pos-title">
                        ${this.getAILogo(displayName)}
                        <div style="flex:1;">
                            <div class="pos-name">${displayName}</div>
                            <div style="display:flex;gap:24px;margin-top:8px;">
                                <div class="pos-sub">UNREALIZED P&L: <span class="${unrealizedPnl>=0?'positive':'negative'}" style="font-weight:700;font-size:14px;">${unrealizedPnl>=0?'+':''}$${this.fn(Math.abs(unrealizedPnl))}</span></div>
                                <div class="pos-sub">TOTAL P&L: <span class="${totalPnlAmount>=0?'positive':'negative'}" style="font-weight:700;font-size:14px;">${totalPnlAmount>=0?'+':''}$${this.fn(Math.abs(totalPnlAmount))}</span></div>
                            </div>
                        </div>
                    </div>
                </div>`;
        if (positions.length>0){
            h += `<div class="pos-table-wrapper" data-model="${displayName}" style="overflow-x:auto;"><table class="pos-table" style="min-width:800px;">
                    <thead>
                        <tr>
                            <th style="width:80px;">SIDE</th>
                            <th style="width:100px;">COIN</th>
                            <th style="width:100px;">LEVERAGE</th>
                            <th style="width:140px;">COST</th>
                            <th style="width:140px;">MKT VALUE</th>
                            <th style="width:120px;text-align:right;">TOTAL P&L</th>
                            <th style="width:100px;">EXIT PLAN</th>
                        </tr>
                    </thead>
                    <tbody>`;
            positions.forEach(pos=>{
                const sideText = pos.side==='long'?'LONG':'SHORT';
                const cost = (pos.entry_price||0) * (pos.quantity||0);
                const value = (pos.current_price||pos.entry_price||0) * (pos.quantity||0);
                const net = pos.side==='long' ? (value - cost) : (cost - value);
                const pnlClass = net>=0?'positive':'negative';
                h += `<tr>
                        <td><span class="pos-side-label ${pos.side==='long'?'long':'short'}">${sideText}</span></td>
                        <td><div class="coin-cell">${this.getCoinIcon(pos.symbol)}<span style="color:#fff;font-weight:600;">${pos.symbol}</span></div></td>
                        <td style="color:#fff;">${pos.leverage}X</td>
                        <td style="color:#fff;">$${this.fn(cost)}</td>
                        <td style="color:#fff;">$${this.fn(value)}</td>
                        <td style="text-align:right;"><span class="${pnlClass}" style="font-weight:700;">${net>=0?'+':''}$${this.fn(Math.abs(net))}</span></td>
                        <td><button class="btn-view" data-target="${pos.profit_target||''}" data-stop="${pos.stop_loss||''}" data-invalid="${(pos.invalidation_condition||'').replace(/"/g, '&quot;')}">VIEW</button></td>
                    </tr>`
            });
            h += `</tbody></table></div>`;
        } else {
            h += '<div class="empty-state">暂无持仓</div>'
        }
        h += '</div>';
        // 渲染完成后绑定Drawer
        setTimeout(()=>{
            const container = document.getElementById('positionsList');
            if(!container) return;
            container.querySelectorAll('.btn-view').forEach(btn => {
                btn.addEventListener('click', () => {
                    const target = btn.getAttribute('data-target');
                    const stop = btn.getAttribute('data-stop');
                    const invalid = (btn.getAttribute('data-invalid') || '').replace(/&quot;/g, '"');
                    const overlay = document.getElementById('exitOverlay');
                    const drawer = document.getElementById('exitDrawer');
                    const content = document.getElementById('drawerContent');
                    content.innerHTML = `
                        <div style="margin-bottom:12px;">
                            <div style="color:#666;font-size:12px;">PROFIT TARGET</div>
                            <div class="positive" style="font-weight:700;font-size:16px;">${target?('$'+this.fp(parseFloat(target))):'未设置'}</div>
                        </div>
                        <div style="margin-bottom:12px;">
                            <div style="color:#666;font-size:12px;">STOP LOSS</div>
                            <div class="negative" style="font-weight:700;font-size:16px;">${stop?('$'+this.fp(parseFloat(stop))):'未设置'}</div>
                        </div>
                        ${invalid?`<div style="margin-top:12px;"><div style="color:#666;font-size:12px;margin-bottom:6px;">INVALIDATION CONDITION</div><div style="color:#bbb;line-height:1.6;">${this.escapeHtml(invalid)}</div></div>`:''}
                    `;
                    overlay.classList.remove('hidden');
                    drawer.classList.remove('hidden');
                });
            });
            document.getElementById('drawerClose')?.addEventListener('click', ()=>{
                document.getElementById('exitOverlay')?.classList.add('hidden');
                document.getElementById('exitDrawer')?.classList.add('hidden');
            });
            document.getElementById('exitOverlay')?.addEventListener('click', ()=>{
                document.getElementById('exitOverlay')?.classList.add('hidden');
                document.getElementById('exitDrawer')?.classList.add('hidden');
            });
        }, 100);
        return h;
    }

    async loadModels() {
        try {
            // 直接使用 fetch，不通过 this.api() 以避免添加 edition 前缀
            const response = await fetch('/api/models');
            const models = await response.json();
            const grid = document.getElementById('modelsGridPage');
            if (!grid) return;

            // 按 Edition 分组
            const edition1 = models.filter(m => String(m.edition) === '1');
            const edition2 = models.filter(m => String(m.edition) === '2');
            
            let h = '';
            
            // Edition 1 模型
            if (edition1.length > 0) {
                h += `<h3 style="color:#00ff88;margin-top:20px;margin-bottom:15px;">Edition 1 - Basic</h3>`;
                edition1.forEach(m => {
                    const profitSign = m.profit_loss_percent >= 0 ? '+' : '';
                    const profitClass = m.profit_loss_percent >= 0 ? 'positive' : 'negative';
                    h += `
                        <div class="model-card-full" onclick="window.location.href='/models/${m.id}'" style="cursor:pointer;margin-bottom:15px;">
                            <h3 style="display:flex;align-items:center;gap:10px;">${this.getAILogoSmall(m.name)} ${m.name}</h3>
                            <p><strong>Account Value:</strong> $${this.fn(m.total_value)}</p>
                            <p><strong>Return:</strong> <span class="${profitClass}">${profitSign}${m.profit_loss_percent.toFixed(2)}%</span></p>
                            <p><strong>Win Rate:</strong> ${m.win_rate.toFixed(1)}%</p>
                            <p><strong>Trades:</strong> ${m.trades} (${m.wins}W/${m.losses}L)</p>
                        </div>
                    `;
                });
            }
            
            // Edition 2 模型
            if (edition2.length > 0) {
                h += `<h3 style="color:#00ccff;margin-top:30px;margin-bottom:15px;">Edition 2 - With News 📰</h3>`;
                edition2.forEach(m => {
                    const profitSign = m.profit_loss_percent >= 0 ? '+' : '';
                    const profitClass = m.profit_loss_percent >= 0 ? 'positive' : 'negative';
                    h += `
                        <div class="model-card-full" onclick="window.location.href='/models/${m.id}'" style="cursor:pointer;margin-bottom:15px;">
                            <h3 style="display:flex;align-items:center;gap:10px;">${this.getAILogoSmall(m.name)} ${m.name}</h3>
                            <p><strong>Account Value:</strong> $${this.fn(m.total_value)}</p>
                            <p><strong>Return:</strong> <span class="${profitClass}">${profitSign}${m.profit_loss_percent.toFixed(2)}%</span></p>
                            <p><strong>Win Rate:</strong> ${m.win_rate.toFixed(1)}%</p>
                            <p><strong>Trades:</strong> ${m.trades} (${m.wins}W/${m.losses}L)</p>
                        </div>
                    `;
                });
            }
            
            grid.innerHTML = h;
            console.log(`✓ Loaded ${models.length} models (E1: ${edition1.length}, E2: ${edition2.length})`);
        } catch (error) {
            console.error('Failed to load models:', error);
            const grid = document.getElementById('modelsGridPage');
            if (grid) grid.innerHTML = '<p style="color:red;">Failed to load models</p>';
        }
    }

    getStrategy(name) {
        const m = {
            'QWEN3 MAX': '激进型',
            'DEEPSEEK V3.2': '平衡型',
            'DEEPSEEK CHAT V3.1': '平衡型',  // 兼容旧名称
            'CLAUDE SONNET 4.5': '保守型',
            'GROK 4': '动量型',
            'GEMINI 2.5 PRO': '剥头皮型',
            'GPT 5': '套利型'
        };
        return m[name] || '策略型';
    }

    getDesc(name) {
        const m = {
            'QWEN3 MAX': '阿里巴巴通义千问，追求高收益',
            'DEEPSEEK V3.2': '中国DeepSeek，平衡风险与收益',
            'DEEPSEEK CHAT V3.1': '中国DeepSeek，平衡风险与收益',  // 兼容旧名称
            'CLAUDE SONNET 4.5': 'Anthropic Claude，注重风险控制',
            'GROK 4': 'xAI Grok，追踪市场趋势',
            'GEMINI 2.5 PRO': 'Google Gemini，从小幅波动获利',
            'GPT 5': 'OpenAI GPT，寻找套利机会'
        };
        return m[name] || '智能交易';
    }

    async selectModel(id) {
        console.log('Selecting model ID:', id);
        
        try {
            const data = await this.api(`/api/trader/${id}`);
            console.log('Trader data:', data);
            
            if (data && data.account) {
                // 先更新持仓内容
                this.showPositions(data);
                
                // 然后切换到持仓标签
                console.log('Switching to positions tab...');
                
                // 移除所有active
                document.querySelectorAll('.dtab').forEach(x => x.classList.remove('active'));
                document.querySelectorAll('.detail-pane').forEach(x => x.classList.remove('active'));
                
                // 激活持仓标签（第3个，索引2）
                const tabs = document.querySelectorAll('.dtab');
                if (tabs[2]) {
                    tabs[2].classList.add('active');
                    console.log('Activated tab 3');
                }
                
                const posPane = document.getElementById('panePositions');
                if (posPane) {
                    posPane.classList.add('active');
                    console.log('Activated positions pane');
                } else {
                    console.error('Positions pane not found!');
                }
            } else {
                console.error('Invalid data:', data);
            }
        } catch (e) {
            console.error('Error selecting model:', e);
        }
    }

    showPositions(data) {
        const c = document.getElementById('positionsList');
        if (!c) return;
        
        // 保存当前滚动位置到实例属性
        const tableWrapper = c.querySelector('.positions-table-wrapper');
        if (tableWrapper && tableWrapper.scrollLeft > 0) {
            this.positionsScrollLeft = tableWrapper.scrollLeft;
        }
        
        const account = data.account || {};
        const metrics = data.metrics || {};
        // ✅ 强制使用后端统一数据，不做任何前端计算（优先account，其次metrics）
        const totalPnlAmount = account.total_pnl_amount ?? metrics.total_pnl_amount ?? 0;
        const totalFees = account.fees ?? metrics.total_fees ?? 0;
        const realizedPnl = account.realized_pnl ?? metrics.realized_pnl ?? 0;
        const positions = data.positions || [];
        
        // 完整的AI统计界面（模仿Alpha Arena）
        let h = `
            <div style="background:#0a0a0a;border:1px solid #1a1a1a;border-radius:8px;padding:20px;margin-bottom:20px;">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
                    ${this.getAILogo(account.name)}
                    <div>
                        <h3 style="color:#fff;font-size:18px;margin:0;">${account.name}</h3>
                        <p style="color:#666;font-size:11px;margin:4px 0 0;">Total Account Value: <span style="color:#fff;font-weight:700;">$${this.fn(account.total_value)}</span></p>
                        <p style="color:#666;font-size:11px;margin:4px 0 0;">Available Cash: <span style="color:#fff;font-weight:700;">$${this.fn(metrics.available_cash ?? (account.cash - account.margin_used))}</span></p>
                    </div>
                </div>
                
                <!-- 三栏统计 -->
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px;">
                    <div style="background:#000;padding:14px;border-radius:6px;text-align:center;">
                        <p style="color:#666;font-size:11px;margin:0 0 6px;">Total P&L:</p>
                        <p class="${totalPnlAmount >= 0 ? 'positive' : 'negative'}" style="font-size:16px;font-weight:700;margin:0;">${totalPnlAmount >= 0 ? '+' : ''}$${this.fn(Math.abs(totalPnlAmount))}</p>
                    </div>
                    <div style="background:#000;padding:14px;border-radius:6px;text-align:center;">
                        <p style="color:#666;font-size:11px;margin:0 0 6px;">Total Fees:</p>
                        <p style="color:#fff;font-size:16px;font-weight:700;margin:0;">$${this.fn(totalFees)}</p>
                    </div>
                    <div style="background:#000;padding:14px;border-radius:6px;text-align:center;">
                        <p style="color:#666;font-size:11px;margin:0 0 6px;">Net Realized:</p>
                        <p class="${realizedPnl >= 0 ? 'positive' : 'negative'}" style="font-size:16px;font-weight:700;margin:0;">$${this.fn(realizedPnl)}</p>
                    </div>
                </div>
                
                <!-- 统计信息 -->
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
                    <div style="background:#000;padding:14px;border-radius:6px;">
                        <p style="color:#666;font-size:11px;margin:0 0 8px;">Average Leverage: <span style="color:#fff;font-weight:700;">10x</span></p>
                        <p style="color:#666;font-size:11px;margin:0 0 8px;">Average Confidence: <span style="color:#fff;font-weight:700;">70%</span></p>
                        <p style="color:#666;font-size:11px;margin:0 0 8px;">Biggest Win: <span class="positive" style="font-weight:700;">$${this.fn(account.biggest_win)}</span></p>
                        <p style="color:#666;font-size:11px;margin:0;">Biggest Loss: <span class="negative" style="font-weight:700;">-$${this.fn(Math.abs(account.biggest_loss))}</span></p>
                    </div>
                    <div style="background:#000;padding:14px;border-radius:6px;">
                        <p style="color:#fff;font-size:13px;font-weight:700;margin:0 0 10px;">HOLD TIMES</p>
                        <p style="color:#666;font-size:11px;margin:0 0 6px;">Long: <span class="positive" style="font-weight:700;">${account.wins > 0 ? '50%' : '0%'}</span></p>
                        <p style="color:#666;font-size:11px;margin:0 0 6px;">Short: <span class="negative" style="font-weight:700;">${account.losses > 0 ? '30%' : '0%'}</span></p>
                        <p style="color:#666;font-size:11px;margin:0;">Flat: <span style="color:#999;font-weight:700;">20%</span></p>
                    </div>
                </div>
            </div>
        `;
        
        if (positions && positions.length > 0) {
            h += '<h4 style="color:#fff;font-size:14px;margin-bottom:12px;letter-spacing:1px;">ACTIVE POSITIONS</h4>';
            
            // 表格格式
            h += `
                <div class="positions-table-wrapper" style="background:#0a0a0a;border:1px solid #1a1a1a;border-radius:8px;overflow-x:auto;">
                    <table style="width:100%;min-width:800px;border-collapse:collapse;">
                        <thead>
                            <tr style="background:#000;border-bottom:1px solid #1a1a1a;">
                                <th style="padding:12px;width:80px;text-align:left;color:#666;font-size:11px;font-weight:800;">SIDE</th>
                                <th style="padding:12px;width:100px;text-align:left;color:#666;font-size:11px;font-weight:800;">COIN</th>
                                <th style="padding:12px;width:100px;text-align:left;color:#666;font-size:11px;font-weight:800;">LEVERAGE</th>
                                <th style="padding:12px;width:140px;text-align:left;color:#666;font-size:11px;font-weight:800;">COST</th>
                                <th style="padding:12px;width:140px;text-align:left;color:#666;font-size:11px;font-weight:800;">MKT VALUE</th>
                                <th style="padding:12px;width:120px;text-align:right;color:#666;font-size:11px;font-weight:800;">TOTAL P&L</th>
                                <th style="padding:12px;width:100px;text-align:left;color:#666;font-size:11px;font-weight:800;">EXIT PLAN</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            positions.forEach(pos => {
                const sideText = pos.side === 'long' ? 'LONG' : 'SHORT';
                const sideClass = pos.side === 'long' ? 'positive' : 'negative';
                const cost = (pos.entry_price||0) * (pos.quantity||0);
                const value = (pos.current_price||pos.entry_price||0) * (pos.quantity||0);
                const net = pos.side==='long' ? (value - cost) : (cost - value);
                const pnlClass = net >= 0 ? 'positive' : 'negative';
                const coinIcon = this.getCoinIcon(pos.symbol);
                
                h += `
                    <tr style="border-bottom:1px solid #1a1a1a;">
                        <td style="padding:12px;"><span class="${sideClass}" style="font-weight:700;font-size:12px;">${sideText}</span></td>
                        <td style="padding:12px;">
                            <div style="display:flex;align-items:center;gap:8px;">
                                ${coinIcon}
                                <span style="color:#fff;font-weight:600;font-size:12px;">${pos.symbol}</span>
                            </div>
                        </td>
                        <td style="padding:12px;color:#fff;font-size:12px;">${pos.leverage}X</td>
                        <td style="padding:12px;color:#fff;font-size:12px;">$${this.fn(cost)}</td>
                        <td style="padding:12px;color:#fff;font-size:12px;">$${this.fn(value)}</td>
                        <td style="padding:12px;text-align:right;">
                            <span class="${pnlClass}" style="font-weight:700;font-size:13px;">${net >= 0 ? '+' : ''}$${this.fn(Math.abs(net))}</span>
                        </td>
                        <td style="padding:12px;">
                            <button class="btn-view-old" data-target="${pos.profit_target||''}" data-stop="${pos.stop_loss||''}" data-invalid="${(pos.invalidation_condition||'').replace(/"/g, '&quot;')}" style="background:transparent;border:1px solid #333;color:#999;padding:4px 12px;border-radius:4px;font-size:10px;cursor:pointer;">VIEW</button>
                        </td>
                    </tr>
                `;
            });
            
            h += `
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            h += '<div class="empty-state">暂无持仓</div>';
        }
        
        c.innerHTML = h;
        
        // 恢复滚动位置并添加滚动监听
        setTimeout(() => {
            const newTableWrapper = c.querySelector('.positions-table-wrapper');
            if (newTableWrapper) {
                // 恢复之前保存的滚动位置
                if (this.positionsScrollLeft > 0) {
                    newTableWrapper.scrollLeft = this.positionsScrollLeft;
                }
                
                // 添加滚动事件监听，实时保存位置
                newTableWrapper.addEventListener('scroll', () => {
                    this.positionsScrollLeft = newTableWrapper.scrollLeft;
                });
            }
        }, 0);
        
        // 绑定旧版 VIEW 按钮
        setTimeout(() => {
            c.querySelectorAll('.btn-view-old').forEach(btn => {
                btn.addEventListener('click', () => {
                    const target = btn.getAttribute('data-target');
                    const stop = btn.getAttribute('data-stop');
                    const invalid = btn.getAttribute('data-invalid').replace(/&quot;/g, '"');
                    const overlay = document.getElementById('exitOverlay');
                    const drawer = document.getElementById('exitDrawer');
                    const content = document.getElementById('drawerContent');
                    content.innerHTML = `
                        <div style="margin-bottom:12px;">
                            <div style="color:#666;font-size:12px;">PROFIT TARGET</div>
                            <div class="positive" style="font-weight:700;font-size:16px;">${target?('$'+this.fp(parseFloat(target))):'未设置'}</div>
                        </div>
                        <div style="margin-bottom:12px;">
                            <div style="color:#666;font-size:12px;">STOP LOSS</div>
                            <div class="negative" style="font-weight:700;font-size:16px;">${stop?('$'+this.fp(parseFloat(stop))):'未设置'}</div>
                        </div>
                        ${invalid?`<div style="margin-top:12px;"><div style="color:#666;font-size:12px;">INVALIDATION CONDITION</div><div style="color:#bbb;margin-top:6px;line-height:1.6;">${this.escapeHtml(invalid)}</div></div>`:''}
                    `;
                    overlay.classList.remove('hidden');
                    drawer.classList.remove('hidden');
                });
            });
        }, 100);
    }

    getCoinIcon(symbol) {
        const icons = {
            'BTC': '<img src="https://s2.coinmarketcap.com/static/img/coins/64x64/1.png" width="20" height="20" style="border-radius:50%">',
            'ETH': '<img src="https://s2.coinmarketcap.com/static/img/coins/64x64/1027.png" width="20" height="20" style="border-radius:50%">',
            'SOL': '<img src="https://s2.coinmarketcap.com/static/img/coins/64x64/5426.png" width="20" height="20" style="border-radius:50%">',
            'BNB': '<img src="https://s2.coinmarketcap.com/static/img/coins/64x64/1839.png" width="20" height="20" style="border-radius:50%">',
            'DOGE': '<img src="https://s2.coinmarketcap.com/static/img/coins/64x64/74.png" width="20" height="20" style="border-radius:50%">',
            'XRP': '<img src="https://s2.coinmarketcap.com/static/img/coins/64x64/52.png" width="20" height="20" style="border-radius:50%">'
        };
        return icons[symbol] || '⚪';
    }

    getAILogo(name) {
        if (name && name.toUpperCase().includes('QWEN')) {
            return '<img src="/static/img/ai/qwen.png?v=2" alt="Qwen" width="56" height="56" style="border-radius:10px;object-fit:contain;" onerror="this.style.display=\'none\'">';
        } else if (name && name.toUpperCase().includes('DEEPSEEK')) {
            return '<img src="/static/img/ai/deepseek.jpg" alt="DeepSeek" width="56" height="56" style="border-radius:10px;object-fit:cover;" onerror="this.style.display=\'none\'">';
        }
        return '<div style="width:56px;height:56px;border-radius:10px;background:#333;"></div>';
    }

    getAILogoSmall(name) {
        if (name && name.toUpperCase().includes('QWEN')) {
            return '<img src="/static/img/ai/qwen.png?v=2" alt="Qwen" width="18" height="18" style="border-radius:4px;object-fit:contain;">';
        } else if (name && name.toUpperCase().includes('DEEPSEEK')) {
            return '<img src="/static/img/ai/deepseek.jpg" alt="DeepSeek" width="18" height="18" style="border-radius:4px;object-fit:cover;">';
        }
        return '';
    }

    async start() {
        await this.api('/api/start');
        console.log('✓ 已启动');
    }

    async stop() {
        await this.api('/api/stop');
        console.log('✓ 已停止');
    }

    async reset() {
        if (confirm('确定重置？')) {
            await this.api('/api/reset');
            location.reload();
        }
    }

    fp(p) {
        if (p >= 1000) return p.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        if (p >= 1) return p.toFixed(2);
        return p.toFixed(6);
    }

    fn(n) {
        return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    formatHoldingTime(seconds) {
        if (seconds < 60) return `${seconds}秒`;
        const mins = Math.floor(seconds / 60);
        if (mins < 60) return `${mins}分钟`;
        const hours = Math.floor(mins / 60);
        const remainMins = mins % 60;
        return `${hours}小时${remainMins}分`;
    }
}

let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new AlphaArena();
    // ⚡ 性能优化：每3秒请求更新（降低服务器压力）
    setInterval(() => {
        if (app.socket?.connected) app.socket.emit('request_update');
    }, 3000);
});
