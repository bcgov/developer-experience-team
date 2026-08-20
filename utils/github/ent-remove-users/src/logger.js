import pino from 'pino';

export const logger = pino(
  {
    level: (process.env.LOG_LEVEL || 'info'),
    timestamp: pino.stdTimeFunctions.isoTime,
    // use standard logging levels rather than pino's numeric logging levels
    formatters: {
      level(label) {
        return { level: label };
      },
    },
  }, 
  pino.transport({
    target: 'pino/file',
    options: { destination: 'info.log' },
  })
);
