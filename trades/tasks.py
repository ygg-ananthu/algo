import logging
from celery import shared_task
from accounts.models import User
from trades.views import OptionTradingBot
from accounts.models import Strategy, UserStrategy


@shared_task
def execute_trading_bot():
    logging.info("Task initialite... ")
    users = User.objects.all()
    for user in users:
        try:
            # Fetch the strategy
            try:
                strategy_obj = Strategy.objects.get(name='option_selling_strategy1')
            except Strategy.DoesNotExist:
                logging.warning(f"Strategy 'option_selling_strategy1' not found for user {user}. Skipping...")
                continue  # Skip to the next user

            # Fetch UserStrategy relation
            try:
                strategy_active = UserStrategy.objects.get(user=user, strategy=strategy_obj)
            except UserStrategy.DoesNotExist:
                logging.warning(f"No active UserStrategy found for {user}. Skipping...")
                continue  # Skip to the next user
            
            # Check if strategy is active
            if not strategy_active.is_active:
                logging.warning(f"Strategy is inactive for {user}. Skipping...")
                continue

            # Initialize bot and execute strategy
            bot = OptionTradingBot(user)
            if bot.access_token:
                logging.info(
                    f"Bot executing strategy: option_selling_strategy1 for {user}")
                bot.execute_strategy()
            else:
                logging.warning(f"Bot access token missing for {user}. Skipping...")

        except Exception as e:
            logging.warning(f"Unexpected error for user {user}: {e}")

