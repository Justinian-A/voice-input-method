import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/voice_service.dart';
import 'settings_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage>
    with SingleTickerProviderStateMixin {
  final VoiceService _voiceService = VoiceService();
  late AnimationController _pulseController;
  bool _connected = false;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
    _connect();
    _voiceService.addListener(_onStateChanged);
  }

  void _onStateChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _connect() async {
    final ok = await _voiceService.connect();
    if (mounted) {
      setState(() => _connected = ok);
    }
  }

  void _toggleListening() {
    if (_voiceService.state == VoiceState.listening ||
        _voiceService.state == VoiceState.processing) {
      _voiceService.stopListening();
    } else {
      _voiceService.startListening();
    }
  }

  void _copyText() {
    if (_voiceService.recognizedText.isNotEmpty) {
      Clipboard.setData(ClipboardData(text: _voiceService.recognizedText));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('已复制到剪贴板'), duration: Duration(seconds: 1)),
      );
    }
  }

  Color _getStateColor() {
    switch (_voiceService.state) {
      case VoiceState.idle:
        return Theme.of(context).colorScheme.primary;
      case VoiceState.listening:
        return Colors.red;
      case VoiceState.processing:
        return Colors.orange;
      case VoiceState.error:
        return Colors.grey;
    }
  }

  IconData _getStateIcon() {
    switch (_voiceService.state) {
      case VoiceState.idle:
        return Icons.mic_none;
      case VoiceState.listening:
        return Icons.mic;
      case VoiceState.processing:
        return Icons.sync;
      case VoiceState.error:
        return Icons.mic_off;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isListening = _voiceService.state == VoiceState.listening ||
        _voiceService.state == VoiceState.processing;

    return Scaffold(
      appBar: AppBar(
        title: const Text('语声'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => SettingsPage(voiceService: _voiceService),
                ),
              );
            },
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // 连接状态
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: _connected
                    ? Colors.green.withAlpha(30)
                    : Colors.red.withAlpha(30),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _connected ? Colors.green : Colors.red,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    _connected ? '服务已连接' : '尝试连接中...',
                    style: TextStyle(
                      color: _connected ? Colors.green : Colors.red,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),

            const Spacer(),

            // 麦克风按钮
            AnimatedBuilder(
              animation: _pulseController,
              builder: (context, child) {
                final scale = isListening
                    ? 1.0 + _pulseController.value * 0.15
                    : 1.0;
                return Transform.scale(
                  scale: scale,
                  child: GestureDetector(
                    onTap: _toggleListening,
                    child: Container(
                      width: 80,
                      height: 80,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: _getStateColor(),
                        boxShadow: [
                          BoxShadow(
                            color: _getStateColor().withAlpha(80),
                            blurRadius: isListening ? 30 : 10,
                            spreadRadius: isListening ? 5 : 0,
                          ),
                        ],
                      ),
                      child: Icon(
                        _getStateIcon(),
                        color: Colors.white,
                        size: 40,
                      ),
                    ),
                  ),
                );
              },
            ),

            const SizedBox(height: 24),

            // 状态文字
            Text(
              isListening ? '正在聆听...' : '点击开始语音输入',
              style: TextStyle(
                fontSize: 16,
                color: Theme.of(context).colorScheme.onSurface,
              ),
            ),

            // 音量指示器
            if (isListening) ...[
              const SizedBox(height: 16),
              SizedBox(
                width: 200,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: _voiceService.audioLevel,
                    minHeight: 6,
                    backgroundColor:
                        Theme.of(context).colorScheme.surfaceContainerHighest,
                  ),
                ),
              ),
            ],

            const Spacer(),

            // 识别结果区域
            if (_voiceService.recognizedText.isNotEmpty)
              Container(
                margin: const EdgeInsets.all(16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Theme.of(context)
                      .colorScheme
                      .surfaceContainerHighest
                      .withAlpha(120),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  children: [
                    Text(
                      _voiceService.recognizedText,
                      style: const TextStyle(fontSize: 18),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 12),
                    OutlinedButton.icon(
                      onPressed: _copyText,
                      icon: const Icon(Icons.copy, size: 16),
                      label: const Text('复制文本'),
                    ),
                  ],
                ),
              ),

            const Spacer(),

            // 底部提示
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                '按 Ctrl+Shift+V 开始/停止语音输入',
                style: TextStyle(
                  fontSize: 12,
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _voiceService.removeListener(_onStateChanged);
    _pulseController.dispose();
    super.dispose();
  }
}
