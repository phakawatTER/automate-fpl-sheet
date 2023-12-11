import argparse
from loguru import logger
from services import FPLService,MessageService
from config import Config


class InvalidInputException(Exception):
    def __init__(self,message:str):
        super().__init__(message)
        self.message = message

def main():
    parser = argparse.ArgumentParser(description="Process the gameweek integer argument.")
    
    # Add the argument for gameweek
    parser.add_argument('--gameweek', type=int, help='Specify the gameweek as an integer')
    
    # Parse the command-line arguments
    args = parser.parse_args()

    # Access the value of the gameweek argument
    gameweek:int = args.gameweek
    if gameweek is None:
        raise InvalidInputException("invalid gameweek value")
    if gameweek < 1 or gameweek > 38:
        raise InvalidInputException("invalid gameweek value. should be in range 1-38")

    logger.info(f"processing gameweek {gameweek}")

    # initialize config
    config = Config.initialize("./config.json")

    # update FPL table
    players = FPLService.update_fpl_table(gameweek,config=config)

    # message_service = MessageService(config=config)
    # message_service.send_gameweek_result_message(players=players,game_week=gameweek)
    

if __name__ == "__main__":
    main()
