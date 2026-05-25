import 'package:flutter/material.dart';
import 'pages/home_page.dart';
import 'services/theme_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const YuShengApp());
}

class YuShengApp extends StatefulWidget {
  const YuShengApp({super.key});

  @override
  State<YuShengApp> createState() => _YuShengAppState();
}

class _YuShengAppState extends State<YuShengApp> {
  final ThemeService _themeService = ThemeService();

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _themeService,
      builder: (context, _) => MaterialApp(
        title: '语声',
        debugShowCheckedModeBanner: false,
        themeMode: _themeService.mode,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF2196F3),
            brightness: Brightness.light,
          ),
          useMaterial3: true,
          fontFamily: 'Microsoft YaHei',
        ),
        darkTheme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF2196F3),
            brightness: Brightness.dark,
          ),
          useMaterial3: true,
          fontFamily: 'Microsoft YaHei',
        ),
        home: HomePage(themeService: _themeService),
      ),
    );
  }
}
