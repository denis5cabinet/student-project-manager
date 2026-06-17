import 'package:flutter/material.dart';
import 'screens/comments_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Comments Client',
      theme: ThemeData.dark(),
      home: const CommentsScreen(taskId: 1), // можно изменить ID задачи
    );
  }
}
