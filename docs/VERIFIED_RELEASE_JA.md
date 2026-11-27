# NIGHT CALENDAR — 本人確認付き GitHub Releases 公開

この方式は Android スマホの操作AIアプリや外部課金サービスを使いません。
GitHub Actions が APK の作成・署名・検証・公開を担当します。

**現時点で公開できない理由**: 長期使用するオーナー署名鍵の安全な登録、およびその鍵で署名したAPKの実機検証が完了していません。QA版は別の鍵です。

## 初回だけ必要な安全準備

1. オーナー管理の長期署名鍵を作り、パスワードとともに独立した保管先2か所へバックアップします。鍵・パスワードを公開リポジトリやチャットに送らないこと。
2. [Androidだけで行う従来のセットアップ](ANDROID_ONLY_SIGNING_JA.md)の方法などで、`release-candidate` GitHub Environment のSecrets 5件を登録します。
3. [GitHub環境設定](https://github.com/kurenn46-max/night-calendar-/settings/environments) で `release-candidate` と `release-publication` のブランチを `main` に限定し、利用できる場合は本人承認（Required reviewers）を設定してください。特に公開環境では承認ルールが実際に有効か確認します。環境名を記載しただけではGitHubの承認保護が有効になるわけではありません。

## 署名済み候補の取得（毎リリース）

1. `main` の [Android APK CI](https://github.com/kurenn46-max/night-calendar-/actions/workflows/android.yml) が緑であることを確認します。
2. [NIGHT CALENDAR Signed Candidate](https://github.com/kurenn46-max/night-calendar-/actions/workflows/signed-candidate.yml) を `main` で手動起動します。
3. 成功したrunの `night-calendar-signed-candidate` 成果物ZIPをダウンロードします。`NIGHT_CALENDAR_candidate.apk` と `SHA256SUMS.txt` が必要です。
4. **このAPKそのもの**をAndroid実機へインストールします。既存のQA版は署名者が異なるため上書きできない場合があります。アプリ設定の保持を確認してから必要ならQA版をアンインストールしてください。同期された予定は端末側のCalendar Providerにあります。
5. Android実機で起動・再起動・月移動・六曜・祝日・予定表示・追加/編集の遷移・ライト/ダーク・権限拒否を確認します。予定名やアカウント内容はGitHubに送らないでください。

## 正式公開（実機合格後のみ）

[Verified Release](https://github.com/kurenn46-max/night-calendar-/actions/workflows/verified-release.yml) の **Run workflow** を `main` から手動起動し、以下4項目を入力します。

| 入力 | 指定値 |
| --- | --- |
| `candidate_run_id` | 署名済み候補を作成したrun ID |
| `tag` | APK内の `versionName` と同じタグ。現在の予定値は `v0.1.0` |
| `expected_apk_sha256` | 候補ZIP内 `SHA256SUMS.txt` の64桁ハッシュ |
| `signed_device_acceptance` | 本番署名APKを実機検証して合格した場合のみ `SIGNED_APK_TESTED` |

このワークフローは以下を自動で確認します。

- GitHubアカウント `kurenn46-max` が `main` から明示操作したこと
- 参照runが `main` の現在のコミットと一致し、署名ワークフローの正常終了・署名ジョブ成功を記録していること
- 同じコミットのAndroid CIが成功していること
- 成果物が該当run由来の有効な署名候補であること
- APKのSHA256、Android署名検証、証明書の存在、アプリID `com.nightcalendar`、バージョンの整合
- 既存の同名タグが存在しないこと

全て合格した場合のみ、**同じ検証済みのAPK**とSHA256SUMSをGitHub Releasesに公開します。署名鍵はワークフローが読み取らず、署名済み候補を検証して公開するだけです。

**注意**: `SIGNED_APK_TESTED` は本人による申告であり、実機テストを技術的に代行・証明するものではありません。GitHub本人認証・リポジトリ環境保護・オーナー承認と併用する必要があります。オーナーのGitHubアカウントが乗っ取られた場合まで完全に防ぐものではありません。

### 更新時

将来APKを更新するときは、同じ長期署名鍵で署名し、`versionCode` を増やし、再度テストと本人承認を行ってください。
鍵を紛失すると既存のインストール版を更新できなくなる可能性があります。

### 作業が止まる時

本番鍵の未登録、GitHub Environmentの安全設定未確認、署名候補runの不合格、実機未確認の場合は**公開しない**のが正しい動作です。
