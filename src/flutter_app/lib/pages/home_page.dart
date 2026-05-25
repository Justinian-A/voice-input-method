import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/voice_service.dart';
import '../services/theme_service.dart';
import 'settings_page.dart';
import 'mic_test_page.dart';

class HomePage extends StatefulWidget {
  final ThemeService themeService;
  const HomePage({super.key, required this.themeService});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage>
    with SingleTickerProviderStateMixin {
  final VoiceService _voiceService = VoiceService();
  late AnimationController _pulseController;
  final ScrollController _scrollController = ScrollController();
  bool _connected = false;
  String _displayedText = '';
  String _lastRecognized = ''; // 上一次的原始结果，用于去重

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
    if (!mounted) return;
    final t = _voiceService.recognizedText;
    if (t.isNotEmpty && t != _lastRecognized) {
      _lastRecognized = t;
      if (_displayedText.isEmpty) {
        _displayedText = t;
      } else {
        // 去重：如果新文本覆盖了旧文本末尾，替换旧内容
        if (t.contains(_displayedText)) {
          _displayedText = t;
        } else {
          _displayedText = '$_displayedText\n$t';
        }
      }
      // 自动滚动到底部
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(
            _scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 200),
            curve: Curves.easeOut,
          );
        }
      });
    }
    setState(() {});
  }

  Future<void> _connect() async {
    final ok = await _voiceService.connect();
    if (mounted) setState(() => _connected = ok);
  }

  void _toggleListening() {
    if (_voiceService.state == VoiceState.listening ||
        _voiceService.state == VoiceState.processing) {
      _voiceService.stopListening();
    } else {
      _displayedText = '';
      _lastRecognized = '';
      _voiceService.startListening();
    }
  }

  void _copyText() {
    if (_displayedText.isNotEmpty) {
      Clipboard.setData(ClipboardData(text: _displayedText));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('已复制到剪贴板'), duration: Duration(seconds: 1)),
      );
    }
  }

  void _clearText() {
    _displayedText = '';
    _lastRecognized = '';
    _scrollController.jumpTo(0);
    setState(() {});
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
            icon: const Icon(Icons.hearing),
            tooltip: '麦克风测试',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => MicTestPage(voiceService: _voiceService),
                ),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => SettingsPage(
                    voiceService: _voiceService,
                    themeService: widget.themeService,
                  ),
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
                    width: 8, height: 8,
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
                      width: 80, height: 80,
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
                      child: Icon(_getStateIcon(), color: Colors.white, size: 40),
                    ),
                  ),
                );
              },
            ),

            const SizedBox(height: 24),

            // 状态文字
            Text(
              isListening ? '正在聆听... 点击停止' : '点击开始语音输入',
              style: TextStyle(
                fontSize: 16,
                color: Theme.of(context).colorScheme.onSurface,
              ),
            ),

            // 音量指示器——独立监听，不触发整页rebuild
            if (isListening) ...[
              const SizedBox(height: 16),
              SizedBox(
                width: 200,
                child: ValueListenableBuilder<double>(
                  valueListenable: _voiceService.audioLevelNotifier,
                  builder: (_, level, __) => ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: level,
                      minHeight: 6,
                      backgroundColor:
                          Theme.of(context).colorScheme.surfaceContainerHighest,
                    ),
                  ),
                ),
              ),
            ],

            const SizedBox(height: 16),

            // 文字显示区——可滚动，占据剩余空间
            Expanded(
              child: Container(
                width: double.infinity,
                margin: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: Theme.of(context)
                      .colorScheme
                      .surfaceContainerHighest
                      .withAlpha(120),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: Theme.of(context).colorScheme.outlineVariant.withAlpha(80),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Expanded(
                      child: SingleChildScrollView(
                        controller: _scrollController,
                        padding: const EdgeInsets.all(16),
                        child: Text(
                          _displayedText.isNotEmpty ? _displayedText : '等待语音输入...',
                          style: TextStyle(
                            fontSize: 18,
                            height: 1.6,
                            color: _displayedText.isNotEmpty
                                ? Theme.of(context).colorScheme.onSurface
                                : Theme.of(context).colorScheme.onSurfaceVariant.withAlpha(120),
                          ),
                        ),
                      ),
                    ),
                    const Divider(height: 1),
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          OutlinedButton.icon(
                            onPressed: _displayedText.isNotEmpty ? _copyText : null,
                            icon: const Icon(Icons.copy, size: 16),
                            label: const Text('复制'),
                          ),
                          const SizedBox(width: 12),
                          OutlinedButton.icon(
                            onPressed: _displayedText.isNotEmpty ? _clearText : null,
                            icon: const Icon(Icons.clear, size: 16),
                            label: const Text('清除'),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 12),

            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                '点击麦克风开始/停止录音',
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
    _scrollController.dispose();
    super.dispose();
  }
}
