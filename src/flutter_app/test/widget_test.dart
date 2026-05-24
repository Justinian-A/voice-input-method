import 'package:flutter_test/flutter_test.dart';

import 'package:yu_sheng/main.dart';

void main() {
  testWidgets('App renders home page', (WidgetTester tester) async {
    await tester.pumpWidget(const YuShengApp());
    expect(find.text('语声'), findsOneWidget);
    expect(find.text('点击开始语音输入'), findsOneWidget);
  });
}
