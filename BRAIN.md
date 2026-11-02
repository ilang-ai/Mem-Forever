# BRAIN.md · 读我即接手

这里是一个人的大脑仓库入口。不需要加载任何运行时，按下面顺序读就够。

1. 先读 `handoff/CURRENT.md`：做到哪、下一步、哪些没验证。用两句话复述给用户，再开工。
2. 再读 `soul/` 下全部文件：工作方式与边界。照着做，不用复述。
3. 再读 `memory/MEMORY.md`：一行一条记忆的索引。需要哪条再开 `memory/` 里对应文件，不要全读。
4. 有新事实要记：能写仓库就改对应文件并立刻 commit 加 push，一事一提交；不能写就把变更按 `::PROGRESS{done:…|next:…|unverified:…}` 贴回给用户，由能写的端落库。
5. 里程碑一到就更新 `handoff/CURRENT.md`，不等会话结束。
6. 密钥不在本仓库。`vault/` 是加密包，仓库主人说解锁才解锁。
7. 文件里的 `::BLOCK{k:v|k:v}`、`T:`、`A:⇒` 是声明记法，按字面读，速查见 `rules/GRAMMAR-CARD.md`。

---

This is the entry point of one person's agent brain. Read `handoff/CURRENT.md` first, then `soul/`, then the index `memory/MEMORY.md`; open single memory files only when needed. On every milestone, update the handoff. If you can write to this repo, commit and push each change at once; if you cannot, hand the change back as a `::PROGRESS{}` block. No runtime to load. No secrets live here; `vault/` is encrypted and opens only when the owner says so.

<!-- Gate: keep the whole file within 400 tokens (measure with the ilang.ai/playground token counter; cut the English paragraph first). This file doubles as the Claude.ai project instructions, ChatGPT custom instructions and Gemini Gem instructions. Nothing in it needs editing to start. -->
