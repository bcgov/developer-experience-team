import pino from 'pino';

export function createLogger({
  logFile = 'info.log',
  logToConsole = false,
  silentInTest = true,
} = {}) {
  const isSilent = silentInTest && process.env.NODE_ENV === 'test';
  const options = {
    level: isSilent ? 'silent' : (process.env.LOG_LEVEL || 'info'),
    timestamp: pino.stdTimeFunctions.isoTime,
    formatters: {
      level(label) {
        return { level: label };
      },
    },
  };

  if (isSilent) {
    return pino(options);
  }

  const streams = [];
  if (logToConsole) {
    streams.push({ stream: process.stdout });
  }
  if (logFile) {
    streams.push({ stream: pino.destination({ dest: logFile, sync: false }) });
  }

  return streams.length > 0 ? pino(options, pino.multistream(streams)) : pino(options);
}