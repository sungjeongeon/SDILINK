package com.sdilink.battery.dev.approval.dto;

import java.time.LocalDateTime;

import com.fasterxml.jackson.annotation.JsonFormat;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;

@Getter
@Setter
@ToString
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ApprovalWaitDto {
	private Long id;

	//보험사명
	private String insuranceName;

	//고객명
	private String userName;

	//차량 id
	private Long carId;

	//차량번호
	private String carNumber;

	@JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd", timezone = "Asia/Seoul")
	private LocalDateTime createdAt;
}
