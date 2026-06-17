import 'package:dio/dio.dart';
import '../models/comment.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:5000/api';
  final Dio _dio = Dio(BaseOptions(baseUrl: baseUrl));

  Future<List<Comment>> fetchComments(int taskId) async {
    try {
      final response = await _dio.get('/comments/', queryParameters: {'task_id': taskId});
      if (response.statusCode == 200) {
        final data = response.data;
        List<dynamic> commentsJson = data['data'];
        return commentsJson.map((json) => Comment.fromJson(json)).toList();
      } else {
        throw Exception('Failed to load comments');
      }
    } on DioException catch (e) {
      throw Exception('Network error: ${e.message}');
    }
  }
}
