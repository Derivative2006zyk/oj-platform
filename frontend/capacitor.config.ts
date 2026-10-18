import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.ojplatform.app',
  appName: 'OJ Platform',
  webDir: 'dist',
  server: {
    androidScheme: 'http', 
    cleartext: true 
  },
};

export default config;