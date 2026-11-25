import 'package:flutter/material.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

import 'screens/splash_screen.dart';
import 'services/ad_service.dart';
import 'widgets/theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  MobileAds.instance.initialize();
  AdService.instance.preloadRewarded().whenComplete(() {
    runApp(const CvMakerApp());
  });
}

class CvMakerApp extends StatelessWidget {
  const CvMakerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CV Maker Pro',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(),
      home: const SplashScreen(),
    );
  }
}
