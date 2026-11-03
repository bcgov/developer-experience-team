// Polyfills for React Native testing
/* global jest, beforeAll, afterAll */
if (typeof global.self === 'undefined') {
  global.self = global;
}

// Mock react-native
jest.mock('react-native', () => ({
  StyleSheet: {
    create: (styles) => styles,
  },
  View: 'View',
  Text: 'Text',
  TouchableOpacity: 'TouchableOpacity',
  ViewStyle: {},
}));

// Suppress console errors during tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('NonSerializableError')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});
