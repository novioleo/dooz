"""Client 主入口"""
import argparse
import logging
import sys
import time

from client.base import Client
from client.brain import BrainClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='dooz Client')
    parser.add_argument('--config', required=True, help='Path to config YAML')
    parser.add_argument('--brain', action='store_true', help='Run as brain (with LLM)')
    parser.add_argument('--llm-key', help='OpenAI API key (if brain mode)')
    args = parser.parse_args()
    
    logger.info(f"Loading config from: {args.config}")
    
    if args.brain:
        logger.info("Starting in BRAIN mode")
        client = BrainClient.from_yaml(args.config)
    else:
        client = Client.from_yaml(args.config)
        
    try:
        client.start()
        logger.info(f"Client {client.device_id} started successfully")
        logger.info(f"Status: {client.get_status()}")
        
        # 保持运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        client.stop()
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
