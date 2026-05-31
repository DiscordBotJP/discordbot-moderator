# discordbot-moderator

Discord サーバー運営向けの補助パネルを提供する既存 Bot です。

## 機能

- `/ログ削除`: チャンネル内のメッセージを条件付きで削除します。
- `/簡易ロールパネル設置ボタン`: メンバーがロールを付け外しできるボタンを設置します。
- `/サークル作成ボタン設置`: メンバーが専用テキストチャンネルを作成できるボタンを設置します。
- `/vc操作パネル設置`: VC設定更新、VC入室者向けスレッド作成、新規VC作成のボタンを設置します。

## 再設計メモ

この repo は既存運用を優先して維持していますが、100体プロジェクトの単機能方針では分割候補です。

- `discordbot-delete-log`
- `discordbot-role-panel`
- `discordbot-circle-room`
- `discordbot-vc-panel`

次に大きな仕様変更を入れる場合は、既存利用状況を確認したうえで単機能 repo へ分割するか判断してください。

## 環境変数

| 変数 | 必須 | 説明 |
| --- | --- | --- |
| `DISCORD_BOT_TOKEN` | はい | Discord Bot token |
| `OPS_LOG_HUB_URL` | いいえ | ops-log-hub 送信先 |
| `OPS_LOG_HUB_KEY` | いいえ | ops-log-hub 送信用 key |
| `OPS_LOG_PROJECT` | いいえ | ops-log project 名。既定値: `discordbot-moderator` |
| `OPS_LOG_ENVIRONMENT` | いいえ | `production` / `development` など |

## 必要権限・Intents

- View Channel
- Send Messages
- Manage Messages
- Manage Channels
- Manage Roles
- Create Public/Private Threads
- Message Content Intent
- Voice States Intent

private thread 内で「メニュー」「ボタン」などの本文に反応するため Message Content Intent が必要です。VC入室状態を使うため Voice States Intent も必要です。

## 運用ログ

`OPS_LOG_HUB_URL` と `OPS_LOG_HUB_KEY` が設定されている場合のみ、以下のイベントを ops-log-hub に送信します。

- `startup`: Bot 起動完了
-- `config_error`: extension 読み込み / command 同期の失敗
- `command_error`: slash command、ボタン、モーダル、thread menu message の失敗

ログには message content や secret 値は含めず、guild/channel/message ID など調査に必要な最小限の情報だけを入れます。

## ローカル実行

```bash
cp .env.example .env
python -m pip install -r requirements.txt
python main.py
```
