import pathlib
from logger_setup import setup_logger # Import the setup function

logger = setup_logger(__name__) # Use the setup function

if created_issues_keys:
    jql = "issuekey in (" + ", ".join(f'"{key}"' for key in created_issues_keys) + ")"
    jira_url_full = f"{JIRA_URL.rstrip('/')}/issues/?jql={jql}"
    
    logger.info("\n--- Process Completed ---")
    logger.info("Link to created Jira issues:")
    logger.info(jira_url_full)

    # Save the link to a file
    try:
        output_link_file = pathlib.Path("jira_results.txt")
        with open(output_link_file, "a", encoding="utf-8") as f:
            f.write(f"{jira_url_full}\n")
        logger.info(f"Jira link also saved to: {output_link_file.resolve()}")
    except IOError as e:
        logger.error(f"Failed to write Jira link to file: {e}")
else:
    logger.info("\n--- Process Completed ---") 