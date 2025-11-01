from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from config import settings
import os
import glob

router = APIRouter()

class PromptUpdateRequest(BaseModel):
    service: str
    name: str
    content: str


@router.get("/list")
async def list_prompts() -> List[Dict[str, Any]]:
    """Возвращает список всех промптов по сервисам."""
    services = []
    
    # Contract Extractor промпты
    contract_prompts_path = "./prompts/contract-extractor"
    if os.path.exists(contract_prompts_path):
        contract_prompts = []
        
        # Основные промпты
        main_prompts = [
            "system.txt",
            "user_template.txt", 
            "summary_system.txt",
            "summary_user_template.txt",
            "field_guidelines.md"
        ]
        
        for prompt_file in main_prompts:
            file_path = os.path.join(contract_prompts_path, prompt_file)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    contract_prompts.append({
                        "name": prompt_file,
                        "content": content,
                        "path": file_path
                    })
                except Exception as e:
                    contract_prompts.append({
                        "name": prompt_file,
                        "content": f"Ошибка чтения: {str(e)}",
                        "path": file_path
                    })
        
        # Промпты полей
        fields_path = "./prompts/contract-extractor/fields"
        if os.path.exists(fields_path):
            field_files = glob.glob(os.path.join(fields_path, "*.md"))
            for field_file in field_files:
                field_name = os.path.basename(field_file)
                try:
                    with open(field_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    contract_prompts.append({
                        "name": f"fields/{field_name}",
                        "content": content,
                        "path": field_file
                    })
                except Exception as e:
                    contract_prompts.append({
                        "name": f"fields/{field_name}",
                        "content": f"Ошибка чтения: {str(e)}",
                        "path": field_file
                    })
        
        services.append({
            "name": "Contract Extractor",
            "prompts": contract_prompts
        })
    
    # Legal AI промпты
    legal_ai_prompts_path = "./prompts/legal-ai"
    if os.path.exists(legal_ai_prompts_path):
        legal_prompts = []
        
        prompt_files = [
            "analyze_system.txt",
            "analyze_user.txt",
            "business_system.txt", 
            "business_user.txt",
            "overview_system.txt",
            "overview_user.txt",
            "analyze_system_lenient_rule.txt"
        ]
        
        for prompt_file in prompt_files:
            file_path = os.path.join(legal_ai_prompts_path, prompt_file)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    legal_prompts.append({
                        "name": prompt_file,
                        "content": content,
                        "path": file_path
                    })
                except Exception as e:
                    legal_prompts.append({
                        "name": prompt_file,
                        "content": f"Ошибка чтения: {str(e)}",
                        "path": file_path
                    })
        
        services.append({
            "name": "Legal AI",
            "prompts": legal_prompts
        })
    
    return services

@router.post("/update")
async def update_prompt(request: PromptUpdateRequest) -> Dict[str, str]:
    """Обновляет содержимое промпта."""
    try:
        # Определяем путь к файлу на основе сервиса
        if request.service == "Contract Extractor":
            if request.name.startswith("fields/"):
                file_path = f"./prompts/contract-extractor/{request.name}"
            else:
                file_path = f"./prompts/contract-extractor/{request.name}"
        elif request.service == "Legal AI":
            file_path = f"./prompts/legal-ai/{request.name}"
        else:
            raise HTTPException(status_code=400, detail="Неизвестный сервис")
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Файл не найден")
        
        # Записываем новый контент
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(request.content)
        
        return {"status": "success", "message": "Промпт успешно обновлен"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении промпта: {str(e)}")


@router.get("/contract-extractor/{prompt_name}")
async def get_contract_extractor_prompt(prompt_name: str) -> Dict[str, str]:
    """Получает содержимое конкретного промпта Contract Extractor."""
    file_path = f"./prompts/contract-extractor/{prompt_name}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения файла: {str(e)}")

@router.get("/legal-ai/{prompt_name}")
async def get_legal_ai_prompt(prompt_name: str) -> Dict[str, str]:
    """Получает содержимое конкретного промпта Legal AI."""
    file_path = f"./prompts/legal-ai/{prompt_name}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения файла: {str(e)}")

