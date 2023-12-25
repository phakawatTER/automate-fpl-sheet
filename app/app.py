from boto3.session import Session
from oauth2client.service_account import ServiceAccountCredentials
import services
import util
from config import Config
from adapter import S3Downloader, GoogleSheet, FPLAdapter, S3Uploader, StateMachine
from database import FirebaseRealtimeDatabase
from line import LineBot

BUCKET = "ds-fpl"


@util.time_track(description="Initialize App")
class App:
    def __init__(self):
        sess = Session()
        self.s3_downloader = S3Downloader(
            session=sess,
            bucket=BUCKET,
            download_dir="/tmp",
        )
        self.s3_uploader = S3Uploader(session=sess, bucket=BUCKET)
        config_path = self.s3_downloader.download_file_from_default_bucket(
            "config.json"
        )
        service_account_cred_path = (
            self.s3_downloader.download_file_from_default_bucket("service_account.json")
        )
        service_account_cred = ServiceAccountCredentials.from_json_keyfile_name(
            service_account_cred_path
        )
        self.config = Config(path_to_config=config_path)
        self.linebot = LineBot(config=self.config)
        self.message_service = services.MessageService(bot=self.linebot)
        google_sheet = GoogleSheet(credential=service_account_cred)

        fpl_adapter = FPLAdapter(cookies=self.config.cookies)

        firebase_db = FirebaseRealtimeDatabase(
            database_url=self.config.firebase_db_url,
            service_account_key_path=service_account_cred_path,
        )
        self.firebase_repo = services.FirebaseRepo(firebase=firebase_db)

        self.fpl_service = services.FPLService(
            config=self.config,
            google_sheet=google_sheet,
            fpl_adapter=fpl_adapter,
            firebase_repo=self.firebase_repo,
        )
        self.subscription_service = services.SubscriptionService(
            fpl_adapter=fpl_adapter,
            firebase_repo=self.firebase_repo,
        )

        self.sfn = StateMachine(session=sess)
