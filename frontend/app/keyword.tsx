import { Stack } from 'expo-router';
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  Button,
  FlatList,
  StyleSheet,
  useColorScheme,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { getAuth, onAuthStateChanged } from 'firebase/auth';
import axios from 'axios';
import { BACKEND_URL } from '@env';

export default function Keyword() {
  const [keywords, setKeywords] = useState([]);
  const [input, setInput] = useState('');
  const [user, setUser] = useState(null);
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const auth = getAuth();

  // ✅ 사용자 감지
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (u) => {
      setUser(u);
    });
    return () => unsubscribe();
  }, []);

  // ✅ 키워드 목록 불러오기
  const fetchKeywords = async (token: string) => {
    try {
      const res = await axios.get(`${BACKEND_URL}/keywords`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setKeywords(res.data);
    } catch (e) {
      console.error('❌ 키워드 불러오기 실패:', e);
    }
  };

  // ✅ 초기 로딩
  useEffect(() => {
    const load = async () => {
      if (!user) return;
      const token = await user.getIdToken();
      fetchKeywords(token);
    };
    load();
  }, [user]);

  // ✅ 키워드 추가
  const handleAdd = async () => {
    if (!input.trim()) return;
    try {
      const token = await user.getIdToken();
      await axios.post(
        `${BACKEND_URL}/keywords`,
        { keyword: input.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setInput('');
      fetchKeywords(token);
    } catch (e) {
      console.error('❌ 키워드 추가 실패:', e);
      Alert.alert('추가 실패', '키워드 추가에 실패했습니다.');
    }
  };

  // ✅ 키워드 삭제
  const handleDelete = async (id: string) => {
    try {
      const token = await user.getIdToken();
      await axios.delete(
        `${BACKEND_URL}/keywords/${id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchKeywords(token);
    } catch (e) {
      console.error('❌ 키워드 삭제 실패:', e);
      Alert.alert('삭제 실패', '키워드 삭제에 실패했습니다.');
    }
  };

  return (
    <>
      <Stack.Screen options={{ title: '키워드 설정' }} />
      <View style={[styles.container, { backgroundColor: isDark ? '#000' : '#fff' }]}>
        <Text style={[styles.title, { color: isDark ? '#fff' : '#000' }]}>키워드 입력</Text>

        <TextInput
          placeholder="예: AI 뉴스"
          placeholderTextColor={isDark ? '#888' : '#aaa'}
          value={input}
          onChangeText={setInput}
          style={[
            styles.input,
            {
              color: isDark ? '#fff' : '#000',
              borderBottomColor: isDark ? '#555' : '#ccc',
            },
          ]}
        />

        <Button title="추가" onPress={handleAdd} />

        <FlatList
          data={keywords}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <View style={styles.itemRow}>
              <Text style={{ color: isDark ? '#fff' : '#000' }}>{item.keyword}</Text>
              <TouchableOpacity onPress={() => handleDelete(item.id)}>
                <Text style={{ color: 'red', marginLeft: 10 }}>삭제</Text>
              </TouchableOpacity>
            </View>
          )}
          ListEmptyComponent={
            <Text style={{ color: isDark ? '#777' : '#666', marginTop: 20 }}>등록된 키워드가 없습니다.</Text>
          }
          style={{ marginTop: 20 }}
        />
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  title: { fontSize: 20, marginBottom: 10 },
  input: {
    borderBottomWidth: 1,
    marginBottom: 10,
    paddingVertical: 8,
    fontSize: 16,
  },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 0.5,
    borderBottomColor: '#ccc',
  },
});
