package com.sdilink.battery.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import com.sdilink.battery.jwt.JwtProvider;
import com.sdilink.battery.jwt.filter.JwtAuthenticationFilter;
import com.sdilink.battery.jwt.service.RedisService;

import lombok.RequiredArgsConstructor;

@Configuration
@RequiredArgsConstructor
@EnableWebSecurity //활성화. 스프링 시큐리티 필터가 스프링 필터체인에 등록됨
public class SecurityConfig extends WebSecurityConfigurerAdapter {

	private final JwtProvider jwtProvider;

	private final RedisService redisService;

	@Override
	protected void configure(HttpSecurity http) throws Exception {
		AuthenticationManager authenticationManager = http.getSharedObject(AuthenticationManager.class);

		//ID, password 문자열을 Base64 로 인코딩하여 전달하는 구조
		http.httpBasic().disable()
			//쿠키 기반이 아닌 JWT 기반이므로 csrf 사용하지 않음
			.csrf().disable()
			.formLogin().disable()
			.cors().configurationSource(corsConfigurationSource())
			.and()
			.sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
			.and()
			.authorizeRequests()
			//.antMatchers("/users/**").hasAuthority("USER")
				/* csv 파일 다운로드 테스트용 */
				.antMatchers("/insurance/api/download").permitAll()
				.antMatchers("/client/expo").permitAll()

			.antMatchers("/insurance/login").permitAll() //insurance로 들어오면 인증이 필요하다
			.antMatchers("/insurance/join").permitAll()
			.antMatchers("/client/login").permitAll()
			.antMatchers("/client/regist").permitAll()
				.antMatchers("/client/carinfos").permitAll()
			.antMatchers("/insurance/api/bms").permitAll()
			//.antMatchers("/client/**").permitAll()
				.antMatchers("/swagger-resources/**").permitAll()
				.antMatchers("/swagger-ui.html", "/webjars/springfox-swagger-ui/**", "/v2/api-docs/**").permitAll()
		.antMatchers("/client").hasAuthority("USER")
			.antMatchers("/insurance").hasAuthority("INSURANCE")
			.anyRequest().authenticated()
			.and()
			//jwt 인증 필터 적용
			.addFilterBefore(new JwtAuthenticationFilter(jwtProvider, redisService), UsernamePasswordAuthenticationFilter.class);
	}

	//passwordEncoder
	@Bean
	public BCryptPasswordEncoder encodePassword() {
		return new BCryptPasswordEncoder();
	}

	@Bean
	public CorsConfigurationSource corsConfigurationSource() {
		CorsConfiguration configuration = new CorsConfiguration();

		configuration.addAllowedOriginPattern("*");
		configuration.addAllowedHeader("*");
		configuration.addAllowedMethod("*");
		configuration.addAllowedHeader("*");
		configuration.addExposedHeader("Authorization");
		configuration.setAllowCredentials(true);

		UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
		source.registerCorsConfiguration("/**", configuration);
		return source;
	}

}
