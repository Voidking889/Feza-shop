from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json

router = APIRouter()

@router.websocket("/ws/track_delivery")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Mock route geometry
    points = [
        {"lat": -6.7266, "lng": 39.2223}, 
        {"lat": -6.7350, "lng": 39.2300},
        {"lat": -6.7420, "lng": 39.2410},
        {"lat": -6.7550, "lng": 39.2500},
        {"lat": -6.7650, "lng": 39.2550},
        {"lat": -6.7760, "lng": 39.2600} 
    ]
    total_distance_km = 8.5
    try:
        total_steps = len(points) - 1
        distance_remaining = total_distance_km
        
        # Initial wait so frontend can catch up
        await asyncio.sleep(1)
        
        for i in range(total_steps):
            start = points[i]
            end = points[i+1]
            frames = 20 # smooth frames per segment
            for j in range(frames + 1):
                progress = j / frames
                current_lat = start["lat"] + (end["lat"] - start["lat"]) * progress
                current_lng = start["lng"] + (end["lng"] - start["lng"]) * progress
                overall_progress = (i + progress) / total_steps
                
                await websocket.send_text(json.dumps({
                    "type": "location_update",
                    "lat": current_lat,
                    "lng": current_lng,
                    "progress": overall_progress,
                    "distance_left": max(0, distance_remaining - ((total_distance_km/total_steps) * progress))
                }))
                await asyncio.sleep(0.5) # 0.5s * 20 = 10 sec per segment
            distance_remaining -= (total_distance_km / total_steps)
            
        await websocket.send_text(json.dumps({
            "type": "arrival",
            "progress": 1.0,
            "distance_left": 0
        }))
    except WebSocketDisconnect:
        print("Driver tracking socket disconnected")
