import pino from 'pino';

const fileStream = pino.destination({ dest: 'info.log', sync: false });

export const logger = pino(
  {
    level: process.env.LOG_LEVEL || 'info',
    timestamp: pino.stdTimeFunctions.isoTime,
    // use standard logging levels rather than pino's numeric logging levels
    formatters: {
      level(label) {
        return { level: label };
      },
    },
  },
  pino.multistream([
    { stream: process.stdout },
    { stream: fileStream },
  ])
);
