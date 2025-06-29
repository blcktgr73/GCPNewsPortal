// app/index.tsx
import { Stack } from 'expo-router';
import React, { useState } from 'react';
import { View, TextInput, Button, Text, Alert, useColorScheme, StyleSheet } from 'react-native';
import { createUserWithEmailAndPassword, signInWithEmailAndPassword } from 'firebase/auth';
import { auth } from '../src/firebaseConfig';
import { useRouter } from 'expo-router';

export default function Index() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const colorScheme = useColorScheme(); // 'dark' | 'light'
  const router = useRouter();

  const handleLogin = async () => {
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      console.log('✅ 로그인 성공:', userCredential.user.email);
      router.replace('/summary');
    } catch (error: any) {
      if (error.code === 'auth/user-not-found') {
        Alert.alert('사용자 없음', '회원가입 후 로그인하세요.');
      } else if (error.code === 'auth/wrong-password') {
        Alert.alert('비밀번호 오류', '비밀번호가 일치하지 않습니다.');
      } else {
        Alert.alert('로그인 실패', error.message);
      }
    }
  };

  const handleSignup = async () => {
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      console.log('✅ 회원가입 성공:', userCredential.user.email);
      router.replace('/keyword');
    } catch (error: any) {
      Alert.alert('회원가입 실패', error.message);
    }
  };

  const isDark = colorScheme === 'dark';

  return (
    <>
      <Stack.Screen options={{ title: '뉴스 요약 로그인',
          headerLeft: () => null, // ← 뒤로가기 버튼 제거
          gestureEnabled: false,  // ← 제스처로도 뒤로 가지 못하게
        }}
      />
      <View style={[styles.container, { backgroundColor: isDark ? '#000' : '#fff' }]}>
        <Text style={[styles.label, { color: isDark ? '#fff' : '#000' }]}>이메일</Text>
        <TextInput
          placeholder="이메일 입력"
          placeholderTextColor={isDark ? '#aaa' : '#666'}
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
          style={[
            styles.input,
            {
              color: isDark ? '#fff' : '#000',
              borderBottomColor: isDark ? '#666' : '#ccc',
            },
          ]}
        />

        <Text style={[styles.label, { color: isDark ? '#fff' : '#000' }]}>비밀번호</Text>
        <TextInput
          placeholder="비밀번호 입력"
          placeholderTextColor={isDark ? '#aaa' : '#666'}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          style={[
            styles.input,
            {
              color: isDark ? '#fff' : '#000',
              borderBottomColor: isDark ? '#666' : '#ccc',
            },
          ]}
        />

        <Button title="로그인" onPress={handleLogin} />
        <View style={{ marginTop: 10 }}>
          <Button title="회원가입" onPress={handleSignup} />
        </View>
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 20 },
  input: {
    borderBottomWidth: 1,
    marginBottom: 20,
    padding: 8,
  },
  label: {
    fontSize: 16,
    marginBottom: 4,
  },
});