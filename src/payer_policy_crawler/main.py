import asyncio
from pathlib import Path

from payer_policy_crawler.checkpoint import Checkpoint
from payer_policy_crawler.config import load_payers
from payer_policy_crawler.http_client import HttpClient
from payer_policy_crawler.output import write_records_csv
from payer_policy_crawler.payer_runner import crawl_payer
from payer_policy_crawler.payer_storage import (
    load_all_payer_records,
    save_payer_records,
)

from payer_policy_crawler.run_logger import RunLogger
from payer_policy_crawler.summary import (
    build_payer_summary,
    write_summary,
)
from payer_policy_crawler.dedup import deduplicate_records

async def run() -> None:
    client = HttpClient()
    checkpoint = Checkpoint()
    logger = RunLogger()

    payer_summaries = []

    try:
        payers = load_payers()
        # payers = [p for p in load_payers() if p["payer_name"] == "UHC"]

        logger.log(
            "run_started",
            payer_count=len(payers),
        )

        for index, payer in enumerate(
            payers,
            start=1,
        ):
            payer_name = payer["payer_name"]
            hint_host = payer["hint_host"]

            status = checkpoint.get_status(
                payer_name
            )

            if status == "completed":
                print(
                    f"[{index}/{len(payers)}] "
                    f"SKIPPED: {payer_name} "
                    f"(already completed)"
                )

                logger.log(
                    "payer_skipped",
                    payer_name=payer_name,
                    reason="already_completed",
                )

                payer_summaries.append(
                    build_payer_summary(
                        payer_name=payer_name,
                        status=status,
                        candidates=0,
                        successful_documents=0,
                        failed_documents=0,
                        notes=[
                            "Already completed "
                            "in a previous run."
                        ],
                    )
                )

                continue

            seed_url = f"https://{hint_host}"

            print("\n" + "=" * 70)
            print(
                f"PAYER {index}/{len(payers)}: "
                f"{payer_name}"
            )
            print(f"Seed: {seed_url}")
            print("=" * 70)

            checkpoint.mark_running(
                payer_name
            )

            logger.log(
                "payer_started",
                payer_name=payer_name,
                payer_index=index,
                payer_count=len(payers),
                seed_url=seed_url,
                previous_status=status,
            )

            try:
                result = await crawl_payer(
                    client=client,
                    payer_name=payer_name,
                    seed_url=seed_url,
                    start_pages=[seed_url],
                )

                save_payer_records(
                    payer_name=payer_name,
                    records=result.records,
                )


                # Persist the discovery result status.
                if result.status == "completed":
                    checkpoint.mark_completed(
                        payer_name
                    )
                elif result.status == "blocked":
                    checkpoint.mark_blocked(
                        payer_name
                    )
                elif result.status == "no_documents_found":
                    checkpoint.mark_no_documents_found(
                        payer_name
                    )
                else:
                    checkpoint.mark_failed(
                        payer_name
                    )

                logger.log(
                    "payer_completed",
                    payer_name=payer_name,
                    status=result.status,
                    candidates=result.candidates,
                    successful_documents=(
                        result.successful_documents
                    ),
                    failed_documents=(
                        result.failed_documents
                    ),
                    record_count=len(result.records),
                    notes=result.notes,
                )

                payer_summaries.append(
                    build_payer_summary(
                        payer_name=payer_name,
                        status=result.status,
                        candidates=result.candidates,
                        successful_documents=(
                            result.successful_documents
                        ),
                        failed_documents=(
                            result.failed_documents
                        ),
                        notes=result.notes,
                    )
                )

                print(
                    f"\n--- {payer_name} SUMMARY ---"
                )
                print(
                    f"Candidates: "
                    f"{result.candidates}"
                )
                print(
                    f"Successful documents: "
                    f"{result.successful_documents}"
                )
                print(
                    f"Failed/skipped: "
                    f"{result.failed_documents}"
                )
                print(
                    f"Status: {result.status.upper()}"
                )

            except KeyboardInterrupt:
                logger.log(
                    "run_interrupted",
                    payer_name=payer_name,
                    payer_index=index,
                )

                print(
                    f"\nInterrupted while processing "
                    f"{payer_name}."
                )
                print(
                    "Completed payers will be skipped "
                    "on the next run."
                )

                raise

            except Exception as exc:
                checkpoint.mark_failed(
                    payer_name
                )

                logger.log(
                    "payer_failed",
                    payer_name=payer_name,
                    payer_index=index,
                    error=str(exc),
                )

                payer_summaries.append(
                    build_payer_summary(
                        payer_name=payer_name,
                        status="failed",
                        candidates=0,
                        successful_documents=0,
                        failed_documents=0,
                        notes=[
                            str(exc)
                        ],
                    )
                )

                print(
                    f"\nFAILED: {payer_name}"
                )
                print(
                    f"Error: {exc}"
                )
                print(
                    "Continuing to the next payer..."
                )

        # -----------------------------------------------------
        # Rebuild final CSV from persisted payer results
        # -----------------------------------------------------
        all_records = load_all_payer_records()

        all_records, duplicate_count = deduplicate_records(
            all_records
        )

        output_path = Path(
            "output/output.csv"
        )

        write_records_csv(
            records=all_records,
            output_path=output_path,
        )

        logger.log(
            "global_deduplication_completed",
            duplicate_count=duplicate_count,
            final_record_count=len(all_records),
        )
        # -----------------------------------------------------
        # Write final summary
        # -----------------------------------------------------

        write_summary(
            payer_summaries=payer_summaries,
        )

        logger.log(
            "run_completed",
            total_documents=len(all_records),
            output_path=str(output_path),
        )

        print("\n" + "=" * 70)
        print("FINAL SUMMARY")
        print("=" * 70)
        print(
            f"Payers configured: {len(payers)}"
        )
        print(
            f"Total persisted documents: "
            f"{len(all_records)}"
        )
        print(
            f"Output: {output_path}"
        )
        print(
            "Summary: output/summary.json"
        )
        print(
            "Run log: output/run_log.jsonl"
        )
        print(
            f"Global duplicates removed: "
            f"{duplicate_count}"
        )
        
    finally:
        await client.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()