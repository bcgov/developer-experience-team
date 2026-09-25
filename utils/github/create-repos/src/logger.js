import pino from 'pino';

//don't log anything when running unit tests
const isTest = process.env.NODE_ENV === 'test';

export const logger = pino(
  {
    level: isTest ? 'silent' : (process.env.LOG_LEVEL || 'info'),
    timestamp: pino.stdTimeFunctions.isoTime,
    // use standard logging levels rather than pino's numeric logging levels
    formatters: {
      level(label) {
        return { level: label };
      },
    },
  }, isTest ? undefined : pino.transport({
  target: 'pino/file',
  options: { destination: 'info.log' },
}));
