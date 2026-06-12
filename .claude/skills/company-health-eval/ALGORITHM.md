# 企业健康度五维评估 — 底层算法详解

> `scripts/score.py` 的完整算法文档。所有分数计算均由此引擎统一执行，确保同指标同分数，消除主观偏差。

---

## 一、算法总览

```
研究数据 → 指标等级判定 → 分值映射 → 维度内等权平均 → 加权求和 → 等级划分
                ↑                              ↑              ↑
          24个指标的定性等级              5个维度0-100分    总分+等级
```

### 1.1 输入

JSON 对象，包含 5 个维度，共 24 个指标（含 1 个加分项）：

```json
{
  "company": "公司英文名",
  "cash_flow":      { 5个指标, 每个取值 healthy|warning|danger },
  "profitability":  { 5个指标, 每个取值 excellent|good|average|alert },
  "debt":           { 5个指标 + 1个加分项 },
  "operations":     { 4个指标 },
  "sustainability": { 5个指标 }
}
```

### 1.2 输出

```json
{
  "company": "公司英文名",
  "scores": { "Cash Flow Quality": 83.0, "Profitability": 87.0, ... },
  "weights": { "Cash Flow Quality": 0.45, ... },
  "total_score": 82.2,
  "grade": "Moderate-High",
  "grade_label": "Moderate-High"
}
```

---

## 二、等级映射表

### 2.1 三维度指标（现金流、偿债、运营、可持续）

使用 `LEVEL_3` 映射表，适用于除盈利能力外的所有维度：

| 等级 | 键名 | 分值 | 含义 |
|------|------|:----:|------|
| 健康 | `healthy` | 90 | 指标处于安全区间，无需关注 |
| 关注 | `warning` | 55 | 指标偏离健康区间，需监控 |
| 危险 | `danger` | 15 | 指标严重恶化，构成实质风险 |

**设计说明**：
- 健康 ≠ 100（满分）。90 分保留了 10 分的容错空间——即使所有指标都是"健康"，仍存在未被指标体系捕获的隐性风险。
- 危险 ≠ 0。15 分是"存在但极差"的下限——只有当指标完全不可测量时才得 0 分。
- 55 和 15 的间距（40 分）大于 90 和 55 的间距（35 分），使得"危险"指标的惩罚比"关注"更重。

### 2.2 四维度指标（盈利能力）

使用 `LEVEL_4` 映射表：

| 等级 | 键名 | 分值 | 含义 |
|------|------|:----:|------|
| 优秀 | `excellent` | 95 | 显著超越行业基准 |
| 良好 | `good` | 75 | 高于行业平均 |
| 一般 | `average` | 50 | 处于行业平均线 |
| 预警 | `alert` | 15 | 显著弱于行业基准 |

### 2.3 研发费用率特殊映射

使用 `LEVEL_RD` 映射表（仅用于 `rd_ratio` 指标）：

| 等级 | 键名 | 分值 | 含义 |
|------|------|:----:|------|
| 优秀 | `excellent` | 95 | 研发费用率 10-25%（科技公司黄金区间） |
| 良好 | `good` | **70** | 研发费用率 5-10% 或 25-35% |
| 一般 | `average` | 50 | 研发费用率 <5% |
| 预警 | `alert` | 15 | 研发费用率 >35% 且公司亏损 |

**为什么 `good` 是 70 而非 75？** 研发费用率的"黄金区间"是非线性的——10-25% 最优，偏离这个区间（无论偏低还是偏高）都不是简单的线性递减。5-10%（偏低）和 25-35%（偏高但仍可控）的惩罚应该比标准四维度的 `good`(75) 略重，以反映研发投入偏离最优区间的风险。

---

## 三、维度一：现金流质量（权重 45%）

最重要的维度。利润是观点，现金流是事实。

### 3.1 指标与判定标准

| # | 指标 | 键名 | 健康 (90) | 关注 (55) | 危险 (15) |
|---|------|------|-----------|-----------|-----------|
| 1 | 经营现金流净额 | `operating_cf` | 连续3年为正 | 时正时负 | 连续为负 |
| 2 | 现金及等价物 | `cash_runway` | 覆盖12个月+运营 | 覆盖6-12个月 | 覆盖<6个月 |
| 3 | 有息负债 | `debt_level` | 0或极低 | 可控 | 高杠杆 |
| 4 | 净现比 | `cf_to_ni_ratio` | >1 | 0.5-1 | <0.5 |

> 应收周转天数（`receivable_turnover`）仅出现在运营效率维度。净现比已间接反映应收账款质量——利润无法转化为现金的首要原因就是回款恶化，无需在现金流维度重复计算。

### 3.2 计算公式

```
score_cash_flow = mean(operating_cf, cash_runway, debt_level, cf_to_ni_ratio)
```

4 个指标等权（各 25%）。

### 3.3 极端场景示例

```
全部 health:          (90+90+90+90)/4 = 90.0
全部 danger:          (15+15+15+15)/4 = 15.0
2H+2W:                (90+90+55+55)/4 = 72.5
2H+1W+1D:             (90+90+55+15)/4 = 62.5
```

---

## 四、维度二：盈利能力（权重 20%）

### 4.1 指标与判定标准

| # | 指标 | 键名 | 优秀 (95) | 良好 (75) | 一般 (50) | 预警 (15) |
|---|------|------|-----------|-----------|-----------|-----------|
| 1 | 毛利率 | `gross_margin` | >行业75分位 | 行业平均+ | 行业平均 | <行业平均80% |
| 2 | 净利率 | `net_margin` | >15%且为正 | 5-15% | 0-5% | 亏损 |
| 3 | 营收增速(3Y CAGR) | `revenue_growth` | >20% | 10-20% | 0-10% | 负增长 |
| 4 | 研发费用率 | `rd_ratio` | 10-25% | 5-10%或25-35% | <5% | >35%且亏损 |
| 5 | 人均产出 | `revenue_per_head` | >行业1.5倍 | 行业平均+ | 行业平均 | <行业80% |

### 4.2 计算公式

```
score_profitability = weighted_mean({
    gross_margin:      0.20 × LEVEL_4[level],
    net_margin:        0.20 × LEVEL_4[level],
    revenue_growth:    0.20 × LEVEL_4[level],
    rd_ratio:          0.20 × LEVEL_RD[level],  // 特殊映射
    revenue_per_head:  0.20 × LEVEL_4[level],
})
```

使用 `_weighted()` 辅助函数。各指标权重均为 0.20，合计 1.0。缺失指标时，已用权重归一化（`total / used_weight`）。

### 4.3 关键边界

| 场景 | gross_margin | net_margin | revenue_growth | rd_ratio | rev_per_head | 维度得分 |
|------|:-----------:|:----------:|:--------------:|:--------:|:------------:|:--------:|
| 全面优秀 | excellent(95) | excellent(95) | excellent(95) | excellent(95) | excellent(95) | 95.0 |
| 全面预警 | alert(15) | alert(15) | alert(15) | alert(15) | alert(15) | 15.0 |
| 典型AI公司 | good(75) | alert(15) | excellent(95) | alert(15) | good(75) | 55.0 |
| 典型消费品 | excellent(95) | excellent(95) | average(50) | good(75) | good(75) | 78.0 |

---

## 五、维度三：偿债能力（权重 15%）

### 5.1 指标与判定标准

| # | 指标 | 键名 | 健康 (90) | 关注 (55) | 危险 (15) |
|---|------|------|-----------|-----------|-----------|
| 1 | 资产负债率 | `debt_to_assets` | <40% | 40-70% | >70% |
| 2 | 有息负债率 | `interest_bearing_debt` | 0% | <20% | >30% |
| 3 | 流动比率 | `current_ratio` | >2 | 1-2 | <1 |
| 4 | 现金比率 | `cash_ratio` | >1 | 0.5-1 | <0.5 |
| 5 | 股权质押比例 | `pledge_ratio` | <30% | 30-60% | >60% |

### 5.2 加分项

```
bonus_zero_debt_tax_a = true  → 维度总分 +5（上限 100）
```

触发条件：公司零有息负债 **且** 税务信用 A 级。该加分项仅在两个条件同时满足时生效。

### 5.3 计算公式

```
base = mean(debt_to_assets, interest_bearing_debt, current_ratio, cash_ratio, pledge_ratio)
if bonus_zero_debt_tax_a:
    score_debt = min(base + 5, 100)
else:
    score_debt = base
```

### 5.4 关键边界

```
全部 health + 加分项:    90 + 5 = 95.0
全部 health 无加分项:    90.0
4H+1W + 加分项:          (90×4+55)/5 + 5 = 88.0
3H+2D:                   (90×3+15×2)/5 = 60.0
全部 danger:              15.0
```

---

## 六、维度四：运营效率（权重 10%）

### 6.1 指标与判定标准

| # | 指标 | 键名 | 健康 (90) | 关注 (55) | 危险 (15) |
|---|------|------|-----------|-----------|-----------|
| 1 | 应收周转 | `receivable_turnover` | <行业平均 | ≈行业平均 | >行业1.5倍 |
| 2 | 客户集中度 | `customer_concentration` | 前5<30% | 30-60% | >60% |
| 3 | 员工规模趋势 | `employee_trend` | 稳定增长 | 持平 | 大幅缩减 |
| 4 | 高管稳定性 | `executive_stability` | 核心团队3年+ | 个别变动 | 批量离职 |

### 6.2 计算公式

```
score_operations = mean(receivable_turnover, customer_concentration, employee_trend, executive_stability)
```

4 个指标等权（各 25%）。


---

## 七、维度五：可持续发展（权重 10%）

### 7.1 指标与判定标准

| # | 指标 | 键名 | 健康 (90) | 关注 (55) | 危险 (15) |
|---|------|------|-----------|-----------|-----------|
| 1 | 行业赛道空间 | `market_growth` | CAGR>15% | 5-15% | <5%或萎缩 |
| 2 | 技术壁垒 | `tech_moat` | 3年+难以复制 | 1-3年 | 无壁垒 |
| 3 | 客户/业务多元化 | `diversification` | 多行业多客户 | 2-3个主要客户 | 依赖单一客户 |
| 4 | 融资/资本支持 | `capital_support` | 上市或强VC背书 | 有融资记录 | 无融资+无盈利 |
| 5 | 政策/监管风险 | `policy_risk` | 政策鼓励 | 中性 | 强监管或政策打压 |

### 7.2 计算公式

```
score_sustainability = mean(market_growth, tech_moat, diversification, capital_support, policy_risk)
```

5 个指标等权（各 20%）。

---

## 八、综合评分

### 8.1 加权公式

```
总分 = CF×0.45 + Profit×0.20 + Debt×0.15 + Ops×0.10 + Sustain×0.10
```

权重设计理念：
- **现金流 45%**：压倒性权重。利润可以粉饰，现金流不会说谎。
- **盈利能力 20%**：重要但次于现金流——亏损的公司可能活很久（靠融资），但现金流断裂的公司会立刻死亡。
- **偿债能力 15%**：杠杆是双刃剑。健康的公司可能因债务结构恶化而猝死。
- **运营效率 10%**：效率影响长期竞争力，但短期不会致命。
- **可持续发展 10%**：赛道、壁垒、政策——决定 5-10 年后的生存概率。

### 8.2 精度处理

```
1. 维度得分在加权前保留一位小数（round to 1 decimal）
2. 加权总分保留一位小数
3. JSON 输出中，total_score 保留一位小数
4. companies.json 中 total 字段四舍五入为整数（round, 非 int 截断）
```

早期版本使用 `int()` 截断（如 78.9 → 78），已修正为 `round()`（78.9 → 79）。

---

## 九、等级划分

```
if   total ≥ 85 → Excellent      (优秀)      财务极稳，适合长期发展
elif total ≥ 70 → Moderate-High  (中等偏上)   稳健型，局部有短板但整体可控
elif total ≥ 55 → Moderate       (中等)      有明确风险点，需具体情况判断
elif total ≥ 40 → Moderate-Low   (中等偏下)   多个风险维度预警，不建议作为首选
else            → High-Risk      (高风险)     重大财务或法律隐患，建议规避
```

边界值属于上一级（≥ 判断）。区间全覆盖，无间隙，无重叠。

### 9.1 等级分布的期望

在 18 家样本公司中（2026-06-12）：

| 等级 | 数量 | 占比 | 典型公司 |
|------|:----:|:----:|----------|
| 优秀 | 2 | 11% | TapTap 88, 欧税通 87 |
| 中等偏上 | 5 | 28% | 汉高 84, 字节跳动 84, iAUTO 82 |
| 中等 | 6 | 33% | DeepSeek 65, 科大讯飞 61, 商汤 55 |
| 中等偏下 | 4 | 22% | 智谱AI 51, 汇纳科技 48, 开普勒 46 |
| 高风险 | 1 | 6% | 云从科技 37 |

分布呈单峰右偏（均值 65.2），中位数约 61。无公司达到严格意义上的 85+ 区间以外的"极端优秀"，也无公司在 40 以下的极端区间（除云从科技外）。

---

## 十、缺失值处理

### 10.1 等权平均（`_average`）

```python
def _average(d, indicators, level_map):
    total = 0.0
    count = 0
    for key in indicators:
        entry = d.get(key)
        if entry is None:
            continue                          # 键不存在 → 跳过
        level = entry if isinstance(entry, str) else entry.get("level")
        if level is None:
            continue                          # 值为 null → 跳过
        total += level_map.get(level, 0)     # 无法识别的等级 → 计0
        count += 1
    return round(total / count, 1) if count > 0 else 0.0
```

**重新加权逻辑**：若 5 个指标中有 1 个缺失，剩余 4 个各占 25%（而非 20%）。这保证了得分始终在 0-100 区间内。

### 10.2 加权平均（`_weighted`）

```python
def _weighted(d, weights, level_maps):
    total = 0.0
    used_weight = 0.0
    for key, weight in weights.items():
        entry = d.get(key)
        if entry is None:
            continue
        level = entry if isinstance(entry, str) else entry.get("level")
        if level is None:
            continue
        level_map = level_maps.get(key, LEVEL_3)
        total += level_map.get(level, 0) * weight
        used_weight += weight
    if used_weight == 0:
        return 0.0
    return round(total / used_weight, 1)     # 归一化
```

**归一化**：`total / used_weight` 而非 `total / 1.0`。若 `rd_ratio` 缺失（权重 0.20），`used_weight = 0.80`，剩余 4 个指标的有效权重各为 0.20/0.80 = 0.25。

### 10.3 空维度

若整个维度的所有指标均缺失（如完全无法获取数据），该维度得分为 0.0，直接拖低总分。这是一种惩罚性设计——数据完全不透明的公司不应获得"中性"评分。

---

## 十一、输入校验

### 11.1 顶层类型检查

```python
if not isinstance(input_data, dict):
    raise TypeError(f"Input must be a JSON object, got {type(input_data).__name__}")
```

防止将数组、字符串或 null 作为输入。

### 11.2 维度 null 保护

```python
def _safe_dim(data, key):
    val = data.get(key) if isinstance(data, dict) else None
    return val if isinstance(val, dict) else {}
```

若某个维度的值为 `null`（而非缺失），返回空字典 `{}`，所有指标视为缺失，该维度得分为 0.0。

### 11.3 未识别等级

`level_map.get(level, 0)` —— 若等级字符串拼写错误（如 `"healhty"`），返回 0 分而非崩溃。但脚本会静默处理，不输出警告。评估者在运行脚本前应人工核对 JSON 中的等级字符串。

---

## 十二、代码调用链

```
main()
  └─ json.load(args.data)
  └─ calculate(input_data)
       ├─ _safe_dim() × 5                      // null保护
       ├─ score_cash_flow()                     // _average × 5指标
       ├─ score_profitability()                 // _weighted × 5指标
       ├─ score_debt()                          // _average × 5 + bonus
       ├─ score_operations()                    // _average × 4指标
       ├─ score_sustainability()                // _average × 5指标
       ├─ sum(scores × weights)                 // 加权求和
       └─ get_grade(total)                      // 等级划分
```

---

## 十三、与旧版评分方法的对比

| 维度 | 旧方法（主观） | 新方法（标准化引擎） |
|------|---------------|---------------------|
| 评分方式 | 基础分 - 扣分项（如"50-15-10-5=20"） | 指标等级 → 固定分值 → 等权平均 |
| 可复现性 | 同一公司不同评估者可能给出不同分数 | 同一指标等级 → 同一分数，100% 确定 |
| 手动调整 | 允许（如迈富时 49→58，TapTap 81→78） | 禁止。所有偏离必须通过修正指标等级反映 |
| 缺失数据处理 | 主观估计 | 自动跳过，权重重新分配 |
| 极端值 | 0 分和 100 分频繁出现 | 15 分下限，90/95 分上限，避免极端 |
| 透明度 | 扣分理由在叙述中，但不可审计 | 每个指标的等级判定可追溯、可辩论 |

---

*算法版本：v1.0 · 最后更新：2026-06-12 · 实现文件：`scripts/score.py`*
