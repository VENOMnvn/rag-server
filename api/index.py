from flask import Flask,request,jsonify
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import string
import random
import os
import whisper
from huggingface_hub.hf_api import HfFolder
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
import pickle
import json
from llamaapi import LlamaAPI
LLAAMA_API = "LL-pm4AWSyNVPn4oMHAiP3R4wHIq5T0bcYP9JzkuqeI9d2csHWnWbxNO9pTWCVF82uY"
llama = LlamaAPI(LLAAMA_API)

model = whisper.load_model("base")
app = Flask(__name__)

HfFolder.save_token('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')

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/")
def hello_world():
    return "<p> Hello ! Server is running fine </p>"

@app.route("/audio",methods =['GET','POST'])
@cross_origin() 
def  getAudio():
        if request.method == 'POST':
        # Ensure 'file' is in the request.files dictionary
               if 'file' not in request.files:
                  return jsonify({"error": "No file part"}), 400
        
               file = request.files['file']
        
         # If user does not select file, browser also submits an empty part without filename
               if file.filename == '':
                     return jsonify({"error": "No selected file"}), 400
        
               if file:
            # Use secure_filename to secure the filename
                 filename = secure_filename(file.filename)
                 save_path = os.path.join(app.instance_path, "audios")
            
              # Ensure the directory exists    
               if not os.path.exists(save_path):
                 os.makedirs(save_path)
            
               # Save the file
               file_to_save = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)) + ".mp3"
               file_path = os.path.join(save_path, file_to_save )
               file.save(file_path)
               print(file_path)
               result = model.transcribe(file_path)
               retreivedText = result["text"]
               splitter = RecursiveCharacterTextSplitter(
                  separators = ["\n\n","\n","."],
                  chunk_size = 200,
                  chunk_overlap = 10
                  )
               split_text = splitter.split_text(retreivedText)
               Docs = []
               for text in split_text :
                   Docs.append(Document(page_content = text))
               db = FAISS.from_documents(Docs, HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5"))

               store_path = "./instance/store/" + file_to_save + ".pkl"

               with open(store_path,"wb") as f :
                  pickle.dump(db,f)

               print("SuccessFully Submitted")
               return jsonify({"message": "File saved successfully","fileName" : file_to_save })
    
        return jsonify({"error": "Invalid request"})


@app.route('/query',methods = ['POST'])
@cross_origin()
def getQuery():
    data = request.get_json()

   #  fileName = request.form.get('fileName')
   #  query = request.form.get('query')
    print(data)

    fileName = data['fileName']
    query = data['query']
    

    with open('./instance/store/' + fileName + '.pkl' ,"rb") as f:
      
      store = pickle.load(f)
      retriever = store.as_retriever()

      result = retriever.invoke(query)
      context  = result[0].page_content

      prompt_template = """
         You are an expert researcher who knows everything about provided context and now you answer given question. Answer based on context do not made up thing 
         on your own
         Question:""" +  query + """ Context: """  + context

      api_request_json = {
      "messages": [
          {"role": "user", "content": prompt_template } ],
       "stream": False,
       "function_call": "get_current_weather",
       }

      # Execute the Request
      response = llama.run(api_request_json)
      return json.dumps(response.json(), indent=2)
       
if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
    app.run()