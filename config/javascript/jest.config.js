module.exports = {
  transform: {
    '^.+\\.tsx?$': 'ts-jest',
    '^.+\\.jsx?$': 'babel-jest'
  },
  testEnvironment: 'node',
  moduleNameMapper: {
    '^@testing-library/react$': '/home/cbwinslow/dev/opendiscourse/opendiscourse/node_modules/@testing-library/react',
    '^react$': '/home/cbwinslow/dev/opendiscourse/opendiscourse/node_modules/react',
    '\\.(jpg|png|gif|svg)$': '<rootDir>/__mocks__/fileMock.js',
    '\\.(css|scss)$': 'identity-namespace'
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  watchPathIgnorePattern: '**/node_modules/**'
};
