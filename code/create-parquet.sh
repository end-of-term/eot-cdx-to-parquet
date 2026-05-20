#!/usr/bin/env bash

# Stop script execution if any command fails
set -e

# Tunables (override via env vars)
: "${DUCKDB_FILENAME:=output.parquet}"
: "${DUCKDB:=duckdb}"
: "${DUCKDB_THREADS:=16}"
: "${DUCKDB_MEM:=8GB}"
: "${DUCKDB_TEMP:=/tmp/duckdb_spill}"
: "${ROW_GROUP_SIZE:=1_000_000}"   # rows per row group (works with preserve_insertion_order=true)

# Run DuckDB, reading data from standard input
duckdb -c "
    -- 1. Configuration Settings
    PRAGMA threads = ${DUCKDB_THREADS};
    PRAGMA memory_limit = '${DUCKDB_MEM}';
    PRAGMA temp_directory = '${DUCKDB_TEMP}';
	PRAGMA disable_print_progress_bar;

    -- Preserve your existing LC_ALL=C sorted order in the write path
    SET preserve_insertion_order = true;

    -- 2. Data Processing & Export
    COPY (
        SELECT
		url_surtkey::VARCHAR                                AS url_surtkey,
		url::VARCHAR                                        AS url,
		url_host_name::VARCHAR                              AS url_host_name,
		url_host_surt::VARCHAR                              AS url_host_surt,
		url_host_canonical::VARCHAR                         AS url_host_canonical,
		NULLIF(url_host_tld, '-')::VARCHAR                  AS url_host_tld,
		NULLIF(url_host_2nd_last_part, '-')::VARCHAR        AS url_host_2nd_last_part,
		NULLIF(url_host_3rd_last_part, '-')::VARCHAR        AS url_host_3rd_last_part,
		NULLIF(url_host_4th_last_part, '-')::VARCHAR        AS url_host_4th_last_part,
		NULLIF(url_host_5th_last_part, '-')::VARCHAR        AS url_host_5th_last_part,
		NULLIF(url_host_registry_suffix, '-')::VARCHAR      AS url_host_registry_suffix,
		NULLIF(url_host_registered_domain, '-')::VARCHAR    AS url_host_registered_domain,
		NULLIF(url_host_private_suffix, '-')::VARCHAR       AS url_host_private_suffix,
		NULLIF(url_host_private_domain, '-')::VARCHAR       AS url_host_private_domain,
		NULLIF(url_host_name_reversed, '-')::VARCHAR        AS url_host_name_reversed,
		NULLIF(url_protocol, '-')::VARCHAR                  AS url_protocol,
		TRY_CAST(NULLIF(url_port, '-') AS INTEGER)          AS url_port,
		NULLIF(url_path, '-')::VARCHAR                      AS url_path,
		NULLIF(url_query, '-')::VARCHAR                     AS url_query,
		STRPTIME(fetch_time, '%Y%m%d%H%M%S')                AS fetch_time,
		TRY_CAST(NULLIF(fetch_status, '-') AS SMALLINT)     AS fetch_status,
		NULLIF(content_digest, '-')::VARCHAR                AS content_digest,
		NULLIF(content_mime_type, '-')::VARCHAR             AS content_mime_type,
		NULLIF(content_mime_detected, '-')::VARCHAR         AS content_mime_detected,
		NULLIF(content_charset, '-')::VARCHAR               AS content_charset,
		NULLIF(content_languages, '-')::VARCHAR             AS content_languages,
		NULLIF(content_puid, '-')::VARCHAR                  AS content_puid,
		NULLIF(warc_filename, '-')::VARCHAR                 AS warc_filename,
		TRY_CAST(NULLIF(warc_record_offset, '-') AS BIGINT) AS warc_record_offset,
		TRY_CAST(NULLIF(warc_record_length, '-') AS BIGINT) AS warc_record_length,
		NULLIF(warc_segment, '-')::VARCHAR                  AS warc_segment,
		NULLIF(crawl, '-')::VARCHAR                         AS crawl,
		NULLIF(subset, '-')::VARCHAR                        AS subset,
		NULLIF(extension, '-')::VARCHAR                           AS extension,
        FROM read_csv(
			'/dev/stdin', 
			delim='\t',
			ignore_errors=true, 
			header=True,
			columns={
				'url_surtkey':'VARCHAR',
				'url':'VARCHAR',
				'url_host_name':'VARCHAR',
				'url_host_surt':'VARCHAR',
				'url_host_canonical':'VARCHAR',
				'url_host_tld':'VARCHAR',
				'url_host_2nd_last_part':'VARCHAR',
				'url_host_3rd_last_part':'VARCHAR',
				'url_host_4th_last_part':'VARCHAR',
				'url_host_5th_last_part':'VARCHAR',
				'url_host_registry_suffix':'VARCHAR',
				'url_host_registered_domain':'VARCHAR',
				'url_host_private_suffix':'VARCHAR',
				'url_host_private_domain':'VARCHAR',
				'url_host_name_reversed':'VARCHAR',
				'url_protocol':'VARCHAR',
				'url_port':'VARCHAR',
				'url_path':'VARCHAR',
				'url_query':'VARCHAR',
				'fetch_time':'VARCHAR',
				'fetch_status':'VARCHAR',
				'content_digest':'VARCHAR',
				'content_mime_type':'VARCHAR',
				'content_mime_detected':'VARCHAR',
				'content_charset':'VARCHAR',
				'content_languages':'VARCHAR',
				'content_puid':'VARCHAR',
				'warc_filename':'VARCHAR',
				'warc_record_offset':'VARCHAR',
				'warc_record_length':'VARCHAR',
				'warc_segment':'VARCHAR',
				'crawl':'VARCHAR',
				'subset':'VARCHAR',
				'extension':'VARCHAR',
			}
        )
    ) 
    TO '${DUCKDB_FILENAME}' (
		FORMAT PARQUET, 
		COMPRESSION ZSTD,
		ROW_GROUP_SIZE ${ROW_GROUP_SIZE}
    );
"

echo "Conversion complete: output.parquet created."
