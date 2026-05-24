import 'package:flutter/material.dart';
import '../services/voice_service.dart';

class MicTestPage extends StatefulWidget {
  final VoiceService voiceService;
  const MicTestPage({super.key, required this.voiceService});

  @override
  State<MicTestPage> createState() => _MicTestPageState();
}

class _MicTestPageState extends State<MicTestPage> {
  double _currentLevel = 0;
  double _maxLevel = 0;
  final List<double> _history = List.filled(40, 0);

  @override
  void initState() {
    super.initState();
    widget.voiceService.audioLevelNotifier.addListener(_onLevel);
  }

  void _onLevel() {
    final level = widget.voiceService.audioLevelNotifier.value;
    setState(() {
      _currentLevel = level;
      if (level > _maxLevel) _maxLevel = level;
      _history.removeAt(0);
      _history.add(level);
    });
  }

  void _startTest() {
    _maxLevel = 0;
    _currentLevel = 0;
    widget.voiceService.startMicTest();
  }

  void _stopTest() {
    widget.voiceService.stopMicTest();
  }

  @override
  Widget build(BuildContext context) {
    final isTesting = widget.voiceService.state == VoiceState.listening ||
        widget.voiceService.state == VoiceState.processing;

    return Scaffold(
      appBar: AppBar(title: const Text('麦克风测试')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            // 实时音量
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Text(
                      isTesting ? '测试中...' : '点击开始测试',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
                    ),
                    const SizedBox(height: 20),
                    // 大音量条
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Container(
                        height: 24,
                        child: LinearProgressIndicator(
                          value: _currentLevel,
                          minHeight: 24,
                          backgroundColor: Theme.of(context).colorScheme.surfaceContainerHighest,
                          color: _currentLevel > 0.3
                              ? Colors.green
                              : _currentLevel > 0.05
                                  ? Colors.orange
                                  : Colors.red,
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '当前音量: ${(_currentLevel * 100).toInt()}%    最大: ${(_maxLevel * 100).toInt()}%',
                      style: const TextStyle(fontSize: 14),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // 波形
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: SizedBox(
                  height: 120,
                  child: CustomPaint(
                    size: const Size(double.infinity, 120),
                    painter: _WavePainter(_history),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 24),

            // 测试按钮
            SizedBox(
              width: 200,
              height: 56,
              child: ElevatedButton.icon(
                onPressed: isTesting ? _stopTest : _startTest,
                icon: Icon(isTesting ? Icons.stop : Icons.mic, size: 28),
                label: Text(isTesting ? '停止测试' : '开始测试'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: isTesting ? Colors.red : Theme.of(context).colorScheme.primary,
                  foregroundColor: Colors.white,
                ),
              ),
            ),

            const Spacer(),

            // 说明
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest.withAlpha(100),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('如何判断麦克风是否正常：', style: TextStyle(fontWeight: FontWeight.bold)),
                  SizedBox(height: 8),
                  Text('1. 点击「开始测试」'),
                  Text('2. 对着麦克风说话'),
                  Text('3. 音量条应该跳动到 30% 以上（绿色）'),
                  Text('4. 波形图应有明显起伏'),
                  SizedBox(height: 8),
                  Text('如果音量始终接近 0%，说明麦克风设备未被正确识别。',
                      style: TextStyle(color: Colors.red)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    widget.voiceService.audioLevelNotifier.removeListener(_onLevel);
    super.dispose();
  }
}

class _WavePainter extends CustomPainter {
  final List<double> data;
  _WavePainter(this.data);

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty) return;
    final paint = Paint()
      ..color = const Color(0xFF2196F3)
      ..strokeWidth = 2
      ..style = PaintingStyle.fill;

    final path = Path();
    final barW = size.width / data.length;

    for (int i = 0; i < data.length; i++) {
      final h = data[i] * size.height;
      final x = i * barW;
      final y = size.height - h;
      path.addRect(Rect.fromLTWH(x + 1, y, barW - 2, h));
    }

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant _WavePainter oldDelegate) => true;
}
