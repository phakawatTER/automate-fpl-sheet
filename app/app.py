from boto3.session import Session
import services
import util
from config import Config
from adapter import S3Downloader, FPLAdapter, S3Uploader, StateMachine, SSM
from database import FirebaseRealtimeDatabase
from line import LineBot

BUCKET = "ds-fpl"


@util.time_track(description="Initialize App")
class App:
    def __init__(self):
        sess = Session()
        ssm = SSM(session=sess)

        self.s3_downloader = S3Downloader(
            session=sess,
            bucket=BUCKET,
            download_dir="/tmp",
        )
        self.s3_uploader = S3Uploader(session=sess, bucket=BUCKET)
        service_account_cred_path = (
            self.s3_downloader.download_file_from_default_bucket("service_account.json")
        )
        self.config = Config.load_from_ssm(ssm)

        self.linebot = LineBot(config=self.config)
        self.message_service = services.MessageService(bot=self.linebot)

        fpl_adapter = FPLAdapter(cookies=self.config.cookies)

        firebase_db = FirebaseRealtimeDatabase(
            database_url=self.config.firebase_db_url,
            service_account_key_path=service_account_cred_path,
        )
        self.firebase_repo = services.FirebaseRepo(firebase=firebase_db)

        self.fpl_service = services.FPLService(
            config=self.config,
            fpl_adapter=fpl_adapter,
            firebase_repo=self.firebase_repo,
        )
        self.subscription_service = services.SubscriptionService(
            fpl_adapter=fpl_adapter,
            firebase_repo=self.firebase_repo,
        )

        self.sfn = StateMachine(session=sess)
