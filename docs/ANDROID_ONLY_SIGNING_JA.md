# NIGHT CALENDAR — Androidスマホだけで本番署名鍵を準備

この手順は **Androidスマホ＋無料のTermux＋GitHub** で完結します。
PCは不要です。秘密鍵とパスワードはチャットや公開GitHubに送らないでください。

**重要：この手順は公開ではありません。** 署名鍵の生成とGitHub Secretsへの
安全な登録だけを行い、正式APKの生成・GitHub Releasesへの公開は行いません。

## 1. TermuxをAndroidにインストール

推奨は公式の [F-Droid版Termux](https://f-droid.org/packages/com.termux/)。
F-Droidアプリ本体をインストールしなくても、TermuxのAPKを直接取得できます。
すでに異なる配布元（Google Play/GitHub）のTermuxを利用中なら、APKを上書きしないでください。

Termuxを起動し、次のコマンドを入力します。

```bash
pkg update -y
pkg install -y openjdk-17 gh openssl coreutils curl gnupg
```

ネット接続とパッケージのインストールが必要です。

## 2. GitHubへスマホからログイン

```bash
gh auth login --web
```

画面の案内に沿ってGitHubの本人アカウントで認証。
認証用コードやGitHubトークンは**ナイトのチャットに送らない**でください。

## 3. スマホで署名鍵を生成し、5つのSecretsを登録

```bash
curl -fL --proto '=https' --tlsv1.2 \
  https://raw.githubusercontent.com/kurenn46-max/night-calendar-/main/scripts/android_release_key_setup.sh \
  -o night-calendar-key.sh
bash -n night-calendar-key.sh
bash night-calendar-key.sh
```

- パスワード（12文字以上）を**スマホ内で2回**入力します。画面に表示されません。
- 初回は専用のRSA署名鍵を生成し、すでに鍵がある場合は上書きせず確認を求めます。
- GitHub CLIを使って次の5項目を `release-candidate` 環境の**暗号化Secrets**へ登録します：
  `NIGHT_CALENDAR_KEYSTORE_B64`、`NIGHT_CALENDAR_KEYSTORE_PASSWORD`、
  `NIGHT_CALENDAR_KEY_ALIAS`、`NIGHT_CALENDAR_KEY_PASSWORD`、
  `NIGHT_CALENDAR_EXPECTED_CERT_SHA256`。
- 登録後は**Secret名だけ**一覧を表示します。値の内容を表示・コピーする必要はありません。
- `release-candidate` 環境を新規作成する場合は `main` のみ許可する保護ルールも設定します。既存環境で `main` 以外が許可されていたら、**秘密情報を送る前に停止**します。その場合はステップ5の設定を先に直して、同じスクリプトを再実行してください（既存鍵は上書きされません）。
- 秘密鍵はTermux専用領域 `~/.local/share/night-calendar-signing/night-calendar-release.jks` に残ります。

> 注意：スマホのOS更新・初期化・Termuxのアンインストールで端末内の秘密鍵を失うと、
> 同じ署名でアプリ更新できなくなる可能性があります。**次のバックアップが必須です。**

## 4. オフ端末の暗号化バックアップを2つ作る

ターミナル内で鍵を暗号化します。

```bash
gpg --symmetric --cipher-algo AES256 \
  --output "$HOME/night-calendar-release.jks.gpg" \
  "$HOME/.local/share/night-calendar-signing/night-calendar-release.jks"
```

GPG用の強いバックアップパスワードを別に設定し、署名パスワードとともに
安全なパスワード管理手段で保管してください。

暗号化済み `.jks.gpg` ファイルを安全なUSBメモリー等に移す場合、初回のみ次を実行します。

```bash
termux-setup-storage
cp "$HOME/night-calendar-release.jks.gpg" "$HOME/storage/downloads/"
```

Androidのファイルアプリから、**暗号化ファイルのみ**をUSBメモリーと
もう1か所の独立した安全な保管先へコピーします。
鍵本体（`.jks`）は共有ストレージ、写真バックアップ、GitHubリポジトリへコピーしないでください。
バックアップ用パスワードも紛失すると復元できません。

## 5. GitHubの環境保護をスマホのブラウザーで確認

[Environment Settings](https://github.com/kurenn46-max/night-calendar-/settings/environments) を開き、
`release-candidate` が存在し、以下を確認します。

- **Deployment branches and tags** を `Selected branches and tags` にし、`main` のみ許可。
- 利用可能な場合は `Required reviewers` で追加承認を設定。
- **Environment secrets** に上記5件の名前が存在することを確認。
- [署名ワークフロー](https://github.com/kurenn46-max/night-calendar-/actions/workflows/signed-candidate.yml) はコードでも `main` からの手動実行のみに制限しています。

## 6. 実際のリリース候補をビルド

キーの2重バックアップと安全設定、CI合格を確認後、
Actionsの `NIGHT CALENDAR Signed Candidate` で `main` を選択し
`Run workflow` を実行します。

完了時は **night-calendar-signed-candidate** というプライベートな
GitHub Actions成果物ができますが、一般公開はされません。
成果物のAPKをAndroid実機にインストールして**署名済み正式候補として**
同期済み予定・六曜・祝日・画面操作・再起動を確認してください。

以前のQA版は**デバッグ鍵で署名**されています。Androidの署名が違うため、
本番署名候補を上書きインストールできないときはQA版をアンインストールします。
予定が端末のカレンダーに同期されていることを事前に確認してください。

すべて通った後、バージョン番号と配布ファイルを最終確認し、
オーナーの明示承認を得て初めてGitHub Releasesに公開します。

- [最終リリース判定表](FINAL_RELEASE_CHECKLIST_JA.md)
- [GitHub公式：Environment Secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets?tool=cli)
- [GitHub CLI公式：gh secret set](https://cli.github.com/manual/gh_secret_set)
- [Termux公式：インストール方法](https://github.com/termux/termux-app#installation)
