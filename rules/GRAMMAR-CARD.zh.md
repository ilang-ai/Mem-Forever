# iLang 记法速查（读大脑用）

- `::NAME{k:v|k2:v2}` 一个声明块。NAME 大写。字段用 | 分隔，键值用 : 分隔。
- `::GENE{名|conf|scope}` 后跟 `T:` 行（特征，「我这样做」）和 `A:x⇒y` 行（反模式，「x 会导致 y，别做」）。
- `conf:tentative|confirmed` 置信度；`scope:global|project` 作用域；`when:条件` 说明何时生效，不是解除指引。
- `@NAME` 大写是实体：人、仓库、机器、任务。
- `::STATE{@X, k:v}` 实体此刻状态。`::FACT{key|value|conf}` 事实。`::PROGRESS{date|done|next|unverified}` 进度。
  `::DECIDE{@X}{what|why|context}` 决定，X＝决定者。`::LESSON{id|type|scope|conf}` 加下一行正文＝教训。
  `::BOUNDARY{never|scope}` 硬边界：永远优先，不随条件变化解除，不给绕过方案。
- 读法：按字面理解键值，不需要字典。不认识的块当带标签的笔记读正文。
- 复述交接单：逐条原文、保留编号、不改写。
- 回写块：整块放三反引号围栏里；键一个不能少，没素材的键写 `无`；发出前数一遍键。
- 不对用户说 DNA、gene、mutation 这些词；说「我记下来了」「上次你说过」。
