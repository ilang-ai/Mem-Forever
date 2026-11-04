# 永久記憶

> **Mem-Forever · セッション横断 · モデル横断 · ツール横断**
> iLang プロトコルで構築された AI 永続記憶層。

[![License](https://img.shields.io/badge/license-MIT-d4a858?style=flat-square)](../LICENSE)
[![Protocol](https://img.shields.io/badge/protocol-iLang_v5.0-d4a858?style=flat-square)](https://ilang.ai)

[English](../README.md) | [中文](README.zh.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt.md) | [Русский](README.ru.md)

> このページは最初の画面のみを扱います。インストール方法、エージェントの動作、計測結果をまとめたエンジニアリングブックは [README.md](../README.md)（英語）と [README.zh.md](README.zh.md)（中国語）です。どちらかを任意の AI エージェントにコピーすれば、実行できます。

---

## 概要

すべてのAIツールはセッション終了後にあなたを忘れる。**Mem-Forever** はGitベースの記憶層で、あらゆるAIツールにあなたを永続的に記憶させる。記憶はプライベートリポジトリにiLang構造化形式で保存される。

コンテキストウィンドウは忘れる。**Mem-Forever は忘れない**。

---

## なぜ

| | |
|---|---|
| **永続** | 一つの記憶が、すべてのセッションとモデル切り替えを超えて存続。 |
| **ポータブル** | `soul/`、`memory/`、`handoff/` のプレーン Markdown。`git diff` で追跡可能。ベンダーロックインなし。 |
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
