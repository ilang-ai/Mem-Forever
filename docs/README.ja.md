# 永久記憶

> **Mem-Forever · セッション横断 · モデル横断 · ツール横断**
> iLang プロトコルで構築された AI 永続記憶層。

[![License](https://img.shields.io/badge/license-MIT-d4a858?style=flat-square)](../LICENSE)
[![Protocol](https://img.shields.io/badge/protocol-iLang_v4.0-d4a858?style=flat-square)](https://ilang.ai)

[English](../README.md) | [中文](README.zh.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt.md) | [Русский](README.ru.md)

> ⚠️ この翻訳はまだ Mem-Forever 1.0 の内容です。2.0 の変更点（新しいレイアウト、ハンドオフ、vault、`brain.py`）は未翻訳です。[README.md](../README.md)（英語）または [README.zh.md](README.zh.md)（中国語）を参照してください。

---

## 概要

すべてのAIツールはセッション終了後にあなたを忘れる。**Mem-Forever** はGitベースの記憶層で、あらゆるAIツールにあなたを永続的に記憶させる。記憶はプライベートリポジトリにiLang構造化形式で保存される。

コンテキストウィンドウは忘れる。**Mem-Forever は忘れない**。

---

## なぜ

| | |
|---|---|
| **永続** | 一つの記憶が、すべてのセッションとモデル切り替えを超えて存続。 |
| **ポータブル** | `.ilang/` のプレーンテキスト。`git diff` で追跡可能。ベンダーロックインなし。 |
| **自動** | AIが会話からプロファイルを自動構築。フォーム記入は不要。 |
| **プライベート** | あなたのリポジトリ、あなたのデータ。サーバーなし、アカウントなし。 |

---

## セットアップ（数秒）

**ステップ1** &ensp; **"Use this template"** → **Create a new repository** → **Private** に設定。

**ステップ2** &ensp; ステップ2はない。

## 別のプロジェクトで作業中？

> *私の記憶リポジトリは `https://github.com/YOUR_USERNAME/brain` にある。そこの `BRAIN.md` を読んでから、ここに戻ってきて。*

リポジトリへのアクセスはエージェントのコネクタ（GitHub 連携）かローカルの clone で与える。トークンをプロンプトに貼らない。

---

## ライセンス

MIT

---

<sub><a href="https://ilang.ai">iLang Protocol</a> · 人工知能のネイティブ言語</sub>
