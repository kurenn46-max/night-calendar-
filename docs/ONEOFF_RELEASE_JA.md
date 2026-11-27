# NIGHT CALENDAR v0.1.0 — 一度だけ使う署名のAndroid APK

## 概要

オーナーから「アプリは今後アップデートしなくてもよい。追加アプリ・Termux・Codespaces・追加課金なしでAPKを公開したい」という方針が示されたため、従来の長期保管用鍵を用いる本番署名の代替として、**GitHub Actions内で1回限りの署名鍵を作り、Android 16エミュレーターで署名済みAPKを実行してからGitHub Releasesへ公開する経路**を追加した。

このAPKは正規のAndroid署名形式を備えるが、**署名用の秘密鍵はランナーから削除され、今後同じ署名者で更新できない**。個人向け・一度きりのサイドロード配布を目的とし、Google Playでの継続的アップデートには適さない。将来置き換える場合は古いアプリをアンインストールする必要がある。Androidカレンダープロバイダに同期した予定はアプリのアンインストールでは消えないが、アプリ固有設定は消える場合がある。

## リリース条件

- 対象: `com.nightcalendar` バージョン `0.1.0`、公開タグ `v0.1.0`
- GitHub Actionsが `app:assembleRelease`、`app:testReleaseUnitTest`、`app:lintRelease` に合格する
- ランナー内の一時鍵を用いて既存の署名スクリプト `scripts/sign_release_candidate.sh` で署名する
- 署名検証、パッケージ/バージョン照合、SHA-256ハッシュ照合
- **配布するのと同一のAPK**でAndroid 16エミュレーターでインストール・診断UI・再起動を検証
- PR段階では公開しない。GitHubリポジトリ `kurenn46-max/night-calendar-` の `main` にこのワークフローファイルがマージされた場合のpushでのみ、タグが未使用であることを確認して一度だけ公開する
- GitHub Releases公開ファイルは `NIGHT_CALENDAR_v0.1.0.apk` と `SHA256SUMS.txt`

## リリース後の実機確認

1. [GitHub Releases](https://github.com/kurenn46-max/night-calendar-/releases)で `v0.1.0` のAPKをダウンロードする。
2. すでにデバッグ署名のQA版が入っている場合は同じパッケージ名のため上書きできない。Androidの同期予定を確認後、必要ならQA版をアンインストールする。**アプリ独自の設定は失われる可能性がある**。
3. ダウンロードしたAPKをインストールし、六曜・祝日・予定表示・月移動・予定の追加/編集・ライト/ダークを確認する。
4. 本番配布APK自体のスマホ実機QAは、ユーザーからの確認をもって完了とする。エミュレーター合格のみを「実機合格」とは書かない。

## 安全な取り扱い

- GitHub Actionsのランナーに作る一時署名鍵は**GitHub Secrets・GitHub Releases・ビルド成果物・チャットに保存しない**。
- APKは公開ファイルなので、中に個人の予定やGitHub秘密情報を含めない。
- 公開済みのタグを上書きしない。公開に失敗した場合は、原因と公開済みアセットを調べてから対応する。
- `docs/FINAL_RELEASE_CHECKLIST_JA.md` と `docs/RELEASE_CANDIDATE.md` は**長期保存する署名鍵による正式更新対応版**の従来手順であり、本ワンオフ版と区別する。
