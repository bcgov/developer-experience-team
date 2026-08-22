import fs from 'fs';
import { logger } from './logger.js';
import { stringify } from 'csv-stringify';
import { pipeline } from 'stream/promises';


/**
 * Writes inactive member results to stdout and a CSV file.
 * @param {Array<import('./enterprise.js').Member>} members
 */
export async function writeReport(members) {

  if (members.length === 0) {
    logger.info('No inactive members found. No report will be generated.');
    return;
  }

  logger.info(`Writing report for ${members.length} inactive member(s)...`);

  const filename = `inactive-users-${new Date().toISOString().slice(0, 10)}.csv`;
  const columns = [
    "userName",
    "email",
    "membership",
    "githubVerifiedDomainEmails"
  ];
  
  const stringifier = stringify({ header: true, columns: columns });
  const writableStream = fs.createWriteStream(filename, { encoding: 'utf8' });
 
  writableStream.on("finish", () => {
     logger.info(`\nReport written to ${filename}`);
  });

  writableStream.on("error", (error) => {
    logger.error("Error writing to file:", error.message);
    throw error;
  });

  await pipeline(
    async function* () {
      for (const row of members) {
        yield row;
      }
    },
    stringifier,
    writableStream
  );
}

