import 'package:flutter/material.dart';
import 'pages/home_page.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const YuShengApp());
}

class YuShengApp extends StatelessWidget {
  const YuShengApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '语声',
      debugShowCheckedModeBanner: false,
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
      home: const HomePage(),
    );
  }
}
