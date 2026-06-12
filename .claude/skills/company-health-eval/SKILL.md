---
name: company-health-eval
description: |
  Evaluate whether a specific company is worth joining as an employee, using a structured 5-dimension framework (cash flow quality, profitability, debt, operations, sustainability) with weighted 0-100 scoring and scenario-based career recommendations. Use this skill whenever the user asks about a named company from a career or employer-due-diligence perspective — especially 「这家公司值不值得去」「帮我评估XX公司」「XX公司靠不靠谱」「XX公司现在还值得去吗」「A和B该选哪个offer」「这家创业公司会不会倒闭」. Also trigger for multi-company career comparisons, startup viability for potential employees, or any question that couples a company name with job-seeking intent (salary, stability, WLB, layoff risk, career growth). Covers Chinese companies (A-share/listed, private, startups) and global ones. Output is structured Chinese with quantified scores and specific recommendations. Do NOT trigger for: pure stock/investment analysis without career context, single-metric questions (e.g. "how to calculate free cash flow"), industry-wide reports without a specific employer, car/product comparisons, or general corporate finance education.
---

# 企业健康度五维评估框架

基于商泰汽车（iAUTO）财务健康评估方法论提炼的通用评估框架。

## 核心原则

- **先快后全**：先给一句话结论和健康等级，再展开完整分析
- **信息交叉**：公开信息搜索 + 用户提供数据，交叉验证，明确标注信息来源和可信度
- **权重优先**：现金流为王（45%），盈利为次（20%），兼顾偿债/运营/成长
- **对标意识**：始终与同行业2-3家可比公司对标，不做孤立判断
- **区分场景**：求职视角侧重稳定性、裁员风险、薪酬竞争力；投资视角侧重成长性、估值、退出路径

## 阶段一：信息收集

### 1.1 主动搜索清单

根据公司类型分渠道搜索：

**所有公司必查：**
- 天眼查/企查查：股权结构、参保人数、工商变更、司法诉讼（筛选「劳动争议」）
- 国家企业信用信息公示系统：社保缴纳人数（验证真实规模）、行政处罚
- 中国裁判文书网：搜索「公司名 + 劳动争议」
- 脉脉/看准网/知乎：员工口碑、离职率、管理层评价

**上市公司加查：**
- 巨潮资讯网/东方财富：近3年财报（营收、净利润、经营现金流、资产负债率、商誉）
- SEC EDGAR（美股中概股）
- 券商研报（东方财富/同花顺/慧博资讯）：行业地位、增长预期

**非上市公司加查：**
- IT桔子/36氪/虎嗅：融资轮次、投资方、估值变化
- 招聘网站（Boss直聘/猎聘）：在招岗位数量与薪资范围（判断增长还是收缩）

### 1.2 向用户确认的信息

搜索无法获取的关键信息，引导用户补充：
- 实际办公地址（vs 注册地）、面试感受、团队氛围
- 口头承诺的薪酬结构、期权条款、竞业限制
- 面试中观察到的人员状态、工位空置率

### 1.3 信息可信度标注

| 标注 | 含义 |
|------|------|
| 🔒 公开财报 | 上市公司经审计数据 |
| 📊 估算 | 基于公开信息推算（标注推算依据） |
| 💬 用户提供 | 用户面试/内部信息 |
| 🌐 网络口碑 | 脉脉/知乎等非正式渠道 |
| ⚠️ 未验证 | 单一来源，无法交叉验证 |

## 阶段二：五维评估

### 维度一：现金流质量（权重 45%）

**这是最重要的维度。利润是观点，现金流是事实。**

| 评估指标 | 健康 | 关注 | 危险 |
|----------|------|------|------|
| 经营现金流净额 | 连续3年为正 | 时正时负 | 连续为负 |
| 现金及等价物 | 覆盖12个月+运营 | 6-12个月 | <6个月 |
| 有息负债 | 0或极低 | 可控 | 高杠杆 |
| 应收周转天数 | <行业平均 | 行业平均 | >行业1.5倍 |
| 净现比（经营现金流/净利润） | >1 | 0.5-1 | <0.5 |

**评分逻辑**：每个指标按三级（健康=90 / 关注=55 / 危险=15）打分，5个指标等权平均得到本维度0-100分。使用 `scripts/score.py` 自动计算，消除主观偏差。

### 维度二：盈利能力（权重 20%）

| 评估指标 | 优秀 | 良好 | 一般 | 预警 |
|----------|------|------|------|------|
| 毛利率 | >行业75分位 | 行业平均+ | 行业平均 | <行业平均80% |
| 净利率 | >15%且为正 | 5-15% | 0-5% | 亏损 |
| 营收增速（3年CAGR） | >20% | 10-20% | 0-10% | 负增长 |
| 研发费用率 | 科技公司10-25% | 5-10%或25-35% | <5% | >35%且亏损 |
| 人均产出 | >行业1.5倍 | 行业平均+ | 行业平均 | <行业80% |

### 维度三：偿债能力（权重 15%）

| 评估指标 | 健康 | 关注 | 危险 |
|----------|------|------|------|
| 资产负债率 | <40% | 40-70% | >70% |
| 有息负债率 | 0% | <20% | >30% |
| 流动比率 | >2 | 1-2 | <1 |
| 现金比率 | >1 | 0.5-1 | <0.5 |
| 股权质押比例 | <30% | 30-60% | >60% |

**加分项**：零有息负债 + 税务信用A级 → 最高评级

### 维度四：运营效率（权重 10%）

| 评估指标 | 健康 | 关注 | 危险 |
|----------|------|------|------|
| 应收周转 | <行业平均 | 行业平均 | >行业1.5倍 |
| 客户集中度 | 前5<30% | 30-60% | >60% |
| 员工规模趋势 | 稳定增长 | 持平 | 大幅缩减 |
| 高管稳定性 | 核心团队3年+ | 个别变动 | 批量离职 |

### 维度五：可持续发展（权重 10%）

| 评估指标 | 健康 | 关注 | 危险 |
|----------|------|------|------|
| 行业赛道空间 | CAGR>15% | 5-15% | <5%或萎缩 |
| 技术壁垒 | 3年+难以复制 | 1-3年 | 无壁垒 |
| 客户/业务多元化 | 多行业多客户 | 2-3个主要客户 | 依赖单一客户 |
| 融资/资本支持 | 上市或强VC背书 | 有融资记录 | 无融资+无盈利 |
| 政策/监管风险 | 政策鼓励 | 中性 | 强监管或政策打压 |

## 阶段三：综合评分（使用标准化评分引擎）

### 评分流程（强制使用 scripts/score.py）

研究完成后，**必须使用标准化评分脚本**计算各维度得分，不再使用主观的"基础分-扣分项"方式。

**Step 1** — 根据研究数据，对每个指标判定等级，写入JSON：

```bash
cat > /tmp/score_input.json << 'JSONEOF'
{
  "company": "<Company English Name>",
  "cash_flow": {
    "operating_cf": "healthy",
    "cash_runway": "healthy",
    "debt_level": "warning",
    "receivable_turnover": "danger",
    "cf_to_ni_ratio": "healthy"
  },
  "profitability": {
    "gross_margin": "good",
    "net_margin": "average",
    "revenue_growth": "excellent",
    "rd_ratio": "excellent",
    "revenue_per_head": "good"
  },
  "debt": {
    "debt_to_assets": "healthy",
    "interest_bearing_debt": "healthy",
    "current_ratio": "warning",
    "cash_ratio": "healthy",
    "pledge_ratio": "healthy",
    "bonus_zero_debt_tax_a": false
  },
  "operations": {
    "receivable_turnover": "danger",
    "customer_concentration": "healthy",
    "employee_trend": "healthy",
    "executive_stability": "warning"
  },
  "sustainability": {
    "market_growth": "healthy",
    "tech_moat": "healthy",
    "diversification": "healthy",
    "capital_support": "warning",
    "policy_risk": "warning"
  }
}
JSONEOF
```

等级映射（详见阶段二各维度指标表）：
- 三维度指标：`healthy`（健康）/ `warning`（关注）/ `danger`（危险）
- 四维度指标（仅盈利能力）：`excellent`（优秀）/ `good`（良好）/ `average`（一般）/ `alert`（预警）

**Step 2** — 运行脚本获得精确分数：

```bash
python3 .claude/skills/company-health-eval/scripts/score.py --data /tmp/score_input.json
```

输出示例：
```
==================================================
  iFLYTEK
==================================================
  Cash Flow Quality                61.0 × 45% =  27.4
  Profitability                    57.0 × 20% =  11.4
  Debt Solvency                    54.0 × 15% =   8.1
  Operational Efficiency           62.5 × 10% =   6.2
  Sustainability                   76.0 × 10% =   7.6
  ────────────────────────────────────────────────
  Total                            60.8 / 100
  Grade                           Moderate
==================================================
```

**Step 3** — 将计算出的分数填入报告的综合评分表，并在报告中保留每个维度的分析叙述（解释为什么每个指标被判定为对应等级）。

**评分引擎规则**（硬编码在 `scripts/score.py` 中，保证每次评估一致）：
- 三维度指标分值：healthy=90, warning=55, danger=15
- 四维度指标分值：excellent=95, good=75, average=50, alert=15
- 研发费用率特殊分值：excellent=95, good=70, average=50, alert=15
- 维度内各指标等权平均；缺失指标自动跳过，权重重新分配
- 偿债能力加分项：零有息负债 + 税务信用A级 → +5分（上限100）

### 加权计算

| 维度 | 权重 | 得分 |
|------|------|------|
| 现金流质量 | 45% | /100 |
| 盈利能力 | 20% | /100 |
| 偿债能力 | 15% | /100 |
| 运营效率 | 10% | /100 |
| 可持续发展 | 10% | /100 |
| **综合得分** | **100%** | **/100** |

### 健康等级

| 得分 | 等级 | 含义 |
|------|------|------|
| 85-100 | 🟢 优秀 | 财务极稳，适合长期发展 |
| 70-85 | 🟡 中等偏上 | 稳健型，局部有短板但整体可控 |
| 55-70 | 🟠 中等 | 有明确风险点，需具体情况判断 |
| 40-55 | 🔴 中等偏下 | 多个风险维度预警，不建议作为首选 |
| <40 | ⚫ 高风险 | 重大财务或法律隐患，建议规避 |

## 阶段四：同业对标

选择2-3家同行业、同规模、同阶段的公司进行关键指标对比：

| 对比项 | 目标公司 | 对标A | 对标B |
|--------|---------|-------|-------|
| 上市/融资状态 | | | |
| 营收规模 | | | |
| 毛利率 | | | |
| 净利率 | | | |
| 员工规模 | | | |
| 核心差异 | | | |

**对标结论**：一句话总结目标公司在行业中的相对位置。

## 阶段五：风险清单

按优先级排列，每项标注：
- 风险等级（高/中高/中/低）
- 具体影响描述（量化 > 定性）
- 触发条件（什么情况下会爆发）

## 阶段六：求职视角（仅在求职场景输出）

如果用户是为了求职，增加以下分析：

### 核心优势
- 稳定性评估：有无裁员记录？行业寒冬期表现如何？
- 技术/业务价值：经验能否带到下一份工作？市场通用性如何？
- 工作强度：996还是965？面试时间/员工状态/加班口碑如何？

### 现存短板
- 薪酬上限：与同行比是高还是低？
- 品牌背书：对下一份工作的跳槽帮助有多大？
- 职业天花板：晋升通道、业务边界、跨领域可能性

### 分场景建议

| 个人诉求 | 推荐 | 次选 | 规避 |
|----------|------|------|------|
| 稳定+深耕 | | | |
| 高薪+跳板 | | | |
| 成长+融资红利 | | | |
| 多元+跨领域 | | | |

## 阶段七：总结

格式：
```
[公司名] 是 [行业] 领域「[定位描述]」的公司：
[一句话核心优势]，唯一短板是 [关键短板]。
在 [行业背景] 大环境下，属于 [风险等级]，适合 [目标人群] 的选择。
```

## 报告模板

生成报告时，使用以下结构：

```
# [公司名] 财务健康评估（评估日期）

## 一句话结论
[健康等级] | [核心标签]

## 一、公司基本画像
- 主体、成立时间、股权结构、规模、主营、资质、融资状态
- 一句话定性

## 二、五维财务健康评估
### 1. 现金流质量（X/100）
### 2. 盈利能力（X/100）
### 3. 偿债能力（X/100）
### 4. 运营效率（X/100）
### 5. 可持续发展能力（X/100）

## 三、综合评分与健康等级
| 维度 | 得分 | 权重 | 加权得分 |

## 四、同业对标

## 五、核心风险清单
1. **风险名（等级）**：描述 + 量化影响

## 六、求职/择业视角（如适用）

## 七、总结
```

## 阶段八：输出归档与软链接

报告和雷达图生成后，必须同步归档到 `company/` 行业分类目录。

### 输出文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 评估报告 | `docs/examples/<公司名>-财务健康评估-YYYY-MM-DD.md` | 中文文件名 |
| 雷达图 | `docs/examples/<公司英文名>_health_radar.png` | 英文文件名（避免CJK字体问题） |

### 行业分类归档

根据公司主营业务确定一级和二级行业，在 `company/` 下创建对应子目录并软链接：

```
company/<一级行业>/<二级行业>/<公司展示名>/
├── <报告>.md  → ../../../../docs/examples/<报告>.md
└── <雷达图>.png → ../../../../docs/examples/<雷达图>.png
```

**步骤：**

1. **确定分类**：参考 `company/README.md` 现有分类体系。若公司行业与现有二级行业均不匹配，新增二级目录；若一级行业也不匹配，新增一级目录。分类以实际主营业务为准，不以工商注册行业为准。

2. **创建目录**：`mkdir -p "company/<一级>/<二级>/<公司展示名>/"`

3. **创建软链接**（相对路径固定为 `../../../../docs/examples/`）：
   ```bash
   ln -sf ../../../../docs/examples/<报告文件名>.md "company/<一级>/<二级>/<公司展示名>/"
   ln -sf ../../../../docs/examples/<雷达图文件名>.png "company/<一级>/<二级>/<公司展示名>/"
   ```

4. **更新索引文件**（每次归档必须执行）：

   a. **`company/README.md`**：
      - 若新增了行业分类（一级或二级），在分类总览树形图中添加新节点
      - 在分类依据表格中添加新行（一级行业、二级行业、公司名、上市状态、综合得分）
   
   b. **`company/index.md`**：
      - 在得分排名表中插入新公司（按得分降序排列，重新编号）
      - 在对应行业分类的表格中添加新公司行
      - 更新统计概览：覆盖公司数 +1、上市/未上市计数、平均得分
      - 若新公司等级区间此前为空（如首次出现 🟢 优秀），更新等级分布计数

5. **验证**：`find "company/<一级>/<二级>/<公司展示名>/" -type l -ls` 确认软链接指向正确。

**公司展示名**：去除股票代码和英文名，使用中文简称。如「商汤科技」「美团」「字节跳动」。

**现有分类速查**（详见 `company/README.md`）：

| 一级行业 | 二级行业 | 已有公司 |
|----------|----------|----------|
| 人工智能 | 计算机视觉 | 商汤科技、云从科技 |
| 互联网平台 | 社交媒体与内容、本地生活 | 字节跳动、美团 |
| 企业服务 | 财税SaaS、营销SaaS | 欧税通、迈富时 |
| 互动娱乐 | 游戏研发、游戏平台 | 叠纸游戏、TapTap |
| 教育科技 | 智慧教育 | 卓越睿新 |
| 汽车科技 | 汽车软件 | 商泰汽车-iAUTO |

## 数据估算规范

当无法获取精确数据时：
- **上市公司**：优先使用财报数据，标注具体年份和来源
- **非上市公司**：基于以下方法估算，必须标注「📊 估算」及推算依据
  - 营收 = 参保人数 × 行业人均产出（注明行业参考值来源）
  - 现金跑道 = 融资总额 × 行业平均消耗率
  - 毛利率/净利率参考同行业上市公司中位值，并说明差异原因
- **区分「事实」vs「估算」vs「推测」**——永远不要让用户误以为估算数据是精确的

## 信息不足时的处理

当无法完成全面评估时：
1. 列出已完成部分和结论
2. 明确列出缺失的关键信息及其重要性
3. 基于已有信息给出「有保留的结论」
4. 给出获取缺失信息的具体建议

## 阶段九：完成后检查清单

每次评估完成后，按顺序逐项验证——**全部打钩才算完成**：

### 文件输出

- [ ] 评估报告已写入 `docs/examples/<公司名>-财务健康评估-YYYY-MM-DD.md`
- [ ] 雷达图已生成 `docs/examples/<公司英文名>_health_radar.png`
- [ ] 两个文件均在 `docs/examples/` 下，实体文件存在（非软链接）

### 评分验证（强制）

**每次评估完成后，必须用评分脚本验证报告中的分数与脚本输出一致。**

- [ ] 评分输入文件已保存（`/tmp/score_input.json`，来自阶段三Step 1）
- [ ] 运行脚本验证分数：

```bash
python3 .claude/skills/company-health-eval/scripts/score.py --data /tmp/score_input.json
```

- [ ] 脚本输出的各维度得分和总分与报告 `## 三、综合评分与健康等级` 中的分数逐项核对一致
- [ ] 若报告中有手动调整（如迈富时从49→58、TapTap从81→78），已移除——标准化引擎不允许主观调整，所有偏离必须通过修正指标等级来反映
- [ ] 雷达图中的数值与脚本输出一致（雷达图由脚本输出JSON生成，自动一致）

**批量核查所有已评估公司分数：**

```bash
# 一键重算全部公司，对比 companies.json 中的分数
python3 -c "
import json, os, subprocess

with open('docs/companies.json') as f:
    companies = json.load(f)

mismatches = []
for c in companies:
    cid = c['id']
    path = f'/tmp/score_inputs/{cid}.json'
    if not os.path.exists(path):
        print(f'  SKIP {c[\"name\"]} — no input file at {path}')
        continue
    r = subprocess.run(['python3', '.claude/skills/company-health-eval/scripts/score.py',
                       '--data', path, '--output', f'/tmp/verify_{cid}.json'],
                      capture_output=True, text=True)
    with open(f'/tmp/verify_{cid}.json') as fh:
        new = json.load(fh)
    old_total = c['total']
    new_total = round(new['total_score'])
    old_dims = {k: c['scores'][k] for k in c['scores']}
    new_dims = {k: int(v) for k, v in new['scores'].items()}
    if old_total != new_total or old_dims != new_dims:
        mismatches.append((c['name'], old_total, new_total, old_dims, new_dims))
        print(f'  MISMATCH {c[\"name\"]}: JSON={old_total} script={new_total}')
    else:
        print(f'  OK {c[\"name\"]}: {new_total}')

if mismatches:
    print(f'\n{mismatches} companies have score drift — regenerate reports and radar charts.')
else:
    print(f'\nAll {len(companies)} companies verified.')
"
```

### 公司归档（软链接）

- [ ] 已确定一级行业和二级行业分类（以实际主营业务为准）
- [ ] 已创建目录 `company/<一级行业>/<二级行业>/<公司展示名>/`
- [ ] 报告软链接已创建：`ln -sf ../../../../docs/examples/<报告>.md "company/<一级>/<二级>/<公司展示名>/"`
- [ ] 雷达图软链接已创建：`ln -sf ../../../../docs/examples/<雷达图>.png "company/<一级>/<二级>/<公司展示名>/"`
- [ ] 已用 `find "company/<一级>/<二级>/<公司展示名>/" -type l -ls` 验证软链接指向正确

### 索引更新

- [ ] `company/README.md` 已更新：
  - 分类总览树形图中已加入新公司（若新增行业则同时添加新目录节点）
  - 分类依据表格中已加入新公司行（一级行业、二级行业、公司名、上市状态、综合得分）
- [ ] `company/index.md` 已更新：
  - 得分排名表中已插入新公司（按得分降序重新排位）
  - 对应行业分类表格中已加入新公司行
  - 统计概览中「覆盖公司」数已 +1，上市/未上市计数已更新，平均得分已重新计算
  - 若新增了等级区间（如首次出现 🟢 优秀），等级分布计数已更新

### 最终验证

- [ ] `git status` 确认所有新增和修改文件已被追踪
- [ ] 提交格式：`feat: evaluate <公司名> with radar chart`
- [ ] 已推送到 `origin/master`

### 前端数据更新

- [ ] `docs/companies.json` 已更新：在数组末尾追加新公司的 JSON 条目（按现有字段结构，`id`/`name`/`nameEn`/`ticker`/`ind1`/`ind2`/`scores`/`total`/`grade`/`gradeLabel`/`oneLine`/`report`/`radar`/`employees`/`revenue`），每行一个对象便于 `git diff` 阅读
- [ ] 若新增一级或二级行业分类，`index.html` 中侧边栏的行业筛选逻辑未硬编码分类列表（当前为动态聚合），无需修改
