import argparse
from datetime import datetime, timedelta, timezone
from typing import Optional

from .client import ChatwootClient
from .extractor import extract_initial_messages
from .report import build_reports, write_reports
from shared.config import get_env, load_env_file
from shared.logger import get_logger


def _parse_since(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--since must be YYYY-MM-DD") from exc


def _get_args() -> argparse.Namespace:
    load_env_file()
    parser = argparse.ArgumentParser(
        description="Extract initial incoming text messages from Chatwoot conversations and generate CSV reports."
    )
    parser.add_argument("--base-url", default=get_env("CHATWOOT_BASE_URL"))
    parser.add_argument("--account-id", default=get_env("CHATWOOT_ACCOUNT_ID"))
    parser.add_argument("--api-token", default=get_env("CHATWOOT_API_ACCESS_TOKEN"))
    parser.add_argument("--inbox-id", default=get_env("CHATWOOT_INBOX_ID"))
    parser.add_argument("--days", type=int, default=get_env("CHATWOOT_DAYS"))
    parser.add_argument("--since", type=_parse_since, default=None)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser


def _validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> argparse.Namespace:
    missing = [
        name
        for name in ("base_url", "account_id", "api_token", "inbox_id")
        if not getattr(args, name)
    ]
    if missing:
        parser.print_help()
        raise SystemExit(f"Missing required parameters: {', '.join(missing)}")
    return args


def _compute_since(args: argparse.Namespace) -> Optional[datetime]:
    if args.since:
        return args.since
    if args.days:
        try:
            days = int(args.days)
        except ValueError as exc:
            raise SystemExit("--days must be an integer") from exc
        return datetime.now(tz=timezone.utc) - timedelta(days=days)
    return None


def main() -> None:
    parser = _get_args()
    args = _validate_args(parser.parse_args(), parser)
    since = _compute_since(args)
    logger = get_logger("cli", level="DEBUG" if args.debug else "INFO")

    client = ChatwootClient(
        base_url=args.base_url,
        account_id=str(args.account_id),
        api_token=args.api_token,
        logger=logger if args.debug else None,
    )

    records, stats = extract_initial_messages(client, str(args.inbox_id), since=since, logger=logger)
    raw_df, literal_df, category_df = build_reports(records)
    write_reports(args.data_dir, raw_df, literal_df, category_df)

    logger.info(f"Total conversaciones listadas: {stats['total_listed']}")
    logger.info(
        f"Total conversaciones procesadas (con mensaje inicial texto): {stats['total_processed']}"
    )
    logger.info(f"Total conversaciones excluidas: {stats['total_excluded']}")

    if not raw_df.empty:
        logger.info("Top 10 literal:")
        for _, row in literal_df.head(10).iterrows():
            logger.info(f"- {row['initial_message_literal']}: {row['cantidad']}")

        logger.info("Top 10 categorias:")
        for _, row in category_df.head(10).iterrows():
            logger.info(f"- {row['category']}: {row['cantidad']}")


if __name__ == "__main__":
    main()
