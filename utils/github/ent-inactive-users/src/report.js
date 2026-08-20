import fs from 'fs/promises';
import { logger } from './logger.js';


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

  const rows = ['userName,email,membership'];

  for (const { userName, email, membership } of members) {
    rows.push([userName, email, membership.join('|')].join(','));
  }

  const filename = `inactive-users-${new Date().toISOString().slice(0, 10)}.csv`;
  await fs.writeFile(filename, rows.join('\n'), 'utf8');
  logger.info(`\nReport written to ${filename}`);
}
