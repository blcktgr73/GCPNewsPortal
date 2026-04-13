import { Stack } from 'expo-router';
import {
  View,
  Text,
  FlatList,
  Button,
  BackHandler,
  StyleSheet,
  useColorScheme,
  TouchableOpacity,
  Linking,
} from 'react-native';
import { useEffect, useState } from 'react';
import { getAuth, onAuthStateChanged, User } from 'firebase/auth';
import axios from 'axios';
import { useRouter } from 'expo-router';
import { BACKEND_URL } from '@env';

interface SummaryItem {
  id: string;
  title: string;
  url: string;
  summary: string;
  created_at?: string;
}

export default function Summary() {
  const [items, setItems] = useState<SummaryItem[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const auth = getAuth();
  const router = useRouter();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';

  // ✅ Back 키 무력화
  useEffect(() => {
    const backHandler = BackHandler.addEventListener('hardwareBackPress', () => true);
    return () => backHandler.remove();
  }, []);

  // ✅ 앱 종료 (Android만 가능, iOS에서는 불가능)
  const exitApp = () => {
    BackHandler.exitApp();
  };

  // ✅ 사용자 상태 감지 및 설정
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
    });
    return () => unsubscribe();
  }, []);

  // ✅ 사용자 토큰 기반 데이터 요청
  useEffect(() => {
    const fetchData = async () => {
      if (!user) return;

      try {
        const token = await user.getIdToken();

        const res = await axios.get(
          `${BACKEND_URL}/summaries`, // ✅ 백틱 사용!
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        setItems(res.data);
      } catch (error) {
        console.error('❌ 요약 데이터 요청 실패:', error);
      }
    };

    fetchData();
  }, [user]);

  // ✅ URL 열기
  const handleOpenURL = async (url: string) => {
    if (await Linking.canOpenURL(url)) {
      Linking.openURL(url);
    } else {
      alert('이 URL을 열 수 없습니다: ' + url);
    }
  };

  return (
    <>
      <Stack.Screen options={{ title: '뉴스 요약',
          headerLeft: () => null,      // 상단 왼쪽 Back 버튼 제거
          gestureEnabled: false,       // 스와이프 제스처도 방지
        }}
      />
      <View style={[styles.container, { backgroundColor: isDark ? '#000' : '#fff' }]}>
        <FlatList
          data={items}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <View style={styles.itemContainer}>
              <Text style={[styles.title, { color: isDark ? '#fff' : '#000' }]}>{item.title}</Text>

              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 4 }}>
                <Text style={{ color: isDark ? '#999' : '#666', fontSize: 12 }}>
                  🕒 {item.created_at ? new Date(item.created_at).toLocaleString() : ''}
                </Text>

                <TouchableOpacity onPress={() => handleOpenURL(item.url)}>
                  <Text style={{ color: isDark ? '#80bfff' : '#0066cc', marginLeft: 10, fontSize: 12 }}>
                    Link
                  </Text>
                </TouchableOpacity>
              </View>              

              <Text style={[styles.summary, { color: isDark ? '#ccc' : '#333' }]}>{item.summary}</Text>
            </View>
          )}
          ListEmptyComponent={
            <Text style={{ textAlign: 'center', color: isDark ? '#999' : '#666', marginTop: 40 }}>
              요약된 뉴스가 없습니다.
            </Text>
          }
        />

        <View style={{ marginTop: 20 }}>
          <Button title="키워드 입력으로 이동" onPress={() => router.push('/keyword')} />
        </View>
        <View style={{ marginTop: 20 }}>
          <Button title="앱 종료" onPress={exitApp} />
        </View>
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  itemContainer: { marginBottom: 20 },
  title: { fontSize: 16, fontWeight: 'bold', marginBottom: 4 },
  summary: { fontSize: 14 },
});
